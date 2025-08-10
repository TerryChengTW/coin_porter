import sys
import asyncio
from typing import Optional, Dict, List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QSplitter,
    QGroupBox, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon

from ..core.exchanges.manager import ExchangeManager
from ..core.config.api_keys import APIKeyManager
from ..core.config.exchanges_config import ExchangeConfigManager
from ..core.exchanges.base import NetworkInfo


class QueryWorker(QThread):
    """背景查詢工作執行緒"""
    finished = Signal(str, object)  # exchange_name, result
    error = Signal(str, str)  # exchange_name, error_message
    
    def __init__(self, exchange_name: str, manager: ExchangeManager, query_type: str, currency: Optional[str] = None):
        super().__init__()
        self.exchange_name = exchange_name
        self.manager = manager
        self.query_type = query_type
        self.currency = currency
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.query_type == "currencies":
                # 獲取單一交易所的支援幣種
                exchange = self.manager._exchanges.get(self.exchange_name)
                if exchange:
                    result = loop.run_until_complete(exchange.get_supported_currencies())
                else:
                    result = []
            elif self.query_type == "networks" and self.currency:
                # 獲取單一交易所的網路資訊
                exchange = self.manager._exchanges.get(self.exchange_name)
                if exchange:
                    result = loop.run_until_complete(exchange.get_currency_networks(self.currency))
                else:
                    result = []
            else:
                result = None
                
            self.finished.emit(self.exchange_name, result)
            
        except Exception as e:
            self.error.emit(self.exchange_name, str(e))
        finally:
            loop.close()


class MainWindow(QMainWindow):
    """Coin Porter 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coin Porter - Cross Exchange Transfer Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化管理器
        self.api_manager = APIKeyManager()
        self.config_manager = ExchangeConfigManager()
        self.exchange_manager = ExchangeManager(self.api_manager)
        
        # 追蹤工作執行緒
        self.workers: List[QueryWorker] = []
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """設定使用者介面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 標題
        title_label = QLabel("Coin Porter")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 建立分頁
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 查詢分頁
        self.setup_query_tab()
        
        # 轉帳分頁
        self.setup_transfer_tab()
        
        # 狀態列
        self.statusBar().showMessage("就緒")
        
    def setup_query_tab(self):
        """設定查詢分頁"""
        query_tab = QWidget()
        self.tab_widget.addTab(query_tab, "幣種查詢")
        
        layout = QVBoxLayout(query_tab)
        
        # 控制面板
        control_group = QGroupBox("查詢控制")
        control_layout = QHBoxLayout(control_group)
        
        # 交易所選擇
        control_layout.addWidget(QLabel("交易所:"))
        self.exchange_combo = QComboBox()
        exchange_names = ["所有交易所"] + self.config_manager.get_exchange_names()
        self.exchange_combo.addItems(exchange_names)
        control_layout.addWidget(self.exchange_combo)
        
        # 幣種輸入
        control_layout.addWidget(QLabel("幣種:"))
        self.currency_combo = QComboBox()
        self.currency_combo.setEditable(True)
        self.currency_combo.addItems(["BTC", "ETH", "USDT", "USDC"])
        control_layout.addWidget(self.currency_combo)
        
        # 查詢按鈕
        self.query_currencies_btn = QPushButton("查詢支援幣種")
        self.query_networks_btn = QPushButton("查詢網路資訊")
        control_layout.addWidget(self.query_currencies_btn)
        control_layout.addWidget(self.query_networks_btn)
        
        control_layout.addStretch()
        layout.addWidget(control_group)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 結果顯示
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "交易所", "幣種", "網路", "最小出金", "手續費", "狀態"
        ])
        
        # 設定表格樣式
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.results_table)
        
        # 日誌顯示
        log_group = QGroupBox("查詢日誌")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
    def setup_transfer_tab(self):
        """設定轉帳分頁"""
        transfer_tab = QWidget()
        self.tab_widget.addTab(transfer_tab, "跨交易所轉帳")
        
        layout = QVBoxLayout(transfer_tab)
        
        # 轉帳控制面板
        transfer_group = QGroupBox("轉帳設定")
        transfer_layout = QVBoxLayout(transfer_group)
        
        # 來源交易所
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("來源交易所:"))
        self.source_exchange = QComboBox()
        self.source_exchange.addItems(self.config_manager.get_exchange_names())
        source_layout.addWidget(self.source_exchange)
        transfer_layout.addLayout(source_layout)
        
        # 目標交易所
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("目標交易所:"))
        self.target_exchange = QComboBox()
        self.target_exchange.addItems(self.config_manager.get_exchange_names())
        target_layout.addWidget(self.target_exchange)
        transfer_layout.addLayout(target_layout)
        
        # 轉帳按鈕
        transfer_btn_layout = QHBoxLayout()
        self.transfer_btn = QPushButton("開始轉帳")
        self.transfer_btn.setEnabled(False)  # 暫時禁用
        transfer_btn_layout.addWidget(self.transfer_btn)
        transfer_btn_layout.addStretch()
        transfer_layout.addLayout(transfer_btn_layout)
        
        layout.addWidget(transfer_group)
        
        # 待實作標籤
        placeholder_label = QLabel("轉帳功能開發中...")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(placeholder_label)
        
        layout.addStretch()
        
    def setup_connections(self):
        """設定信號連接"""
        self.query_currencies_btn.clicked.connect(self.query_currencies)
        self.query_networks_btn.clicked.connect(self.query_networks)
        
    def query_currencies(self):
        """查詢支援幣種"""
        self.log("開始查詢支援幣種...")
        self.show_progress()
        
        selected_exchange = self.exchange_combo.currentText()
        if selected_exchange == "所有交易所":
            exchanges = self.config_manager.get_exchange_names()
        else:
            exchanges = [selected_exchange]
            
        self.clear_results()
        
        for exchange in exchanges:
            worker = QueryWorker(exchange, self.exchange_manager, "currencies")
            worker.finished.connect(self.on_currencies_received)
            worker.error.connect(self.on_query_error)
            self.workers.append(worker)
            worker.start()
            
    def query_networks(self):
        """查詢網路資訊"""
        currency = self.currency_combo.currentText().upper()
        if not currency:
            self.log("請輸入幣種名稱")
            return
            
        self.log(f"開始查詢 {currency} 網路資訊...")
        self.show_progress()
        
        selected_exchange = self.exchange_combo.currentText()
        if selected_exchange == "所有交易所":
            exchanges = self.config_manager.get_exchange_names()
        else:
            exchanges = [selected_exchange]
            
        self.clear_results()
        
        for exchange in exchanges:
            worker = QueryWorker(exchange, self.exchange_manager, "networks", currency)
            worker.finished.connect(self.on_networks_received)
            worker.error.connect(self.on_query_error)
            self.workers.append(worker)
            worker.start()
            
    def on_currencies_received(self, exchange_name: str, currencies: List[str]):
        """處理幣種查詢結果"""
        if currencies:
            self.log(f"{exchange_name.upper()}: 找到 {len(currencies)} 個幣種")
            # 可以考慮將結果顯示在表格中
        else:
            self.log(f"{exchange_name.upper()}: 無法獲取幣種列表")
        
        self.check_all_workers_done()
        
    def on_networks_received(self, exchange_name: str, networks: List[NetworkInfo]):
        """處理網路查詢結果"""
        if networks:
            self.log(f"{exchange_name.upper()}: 找到 {len(networks)} 個網路")
            self.add_networks_to_table(exchange_name, networks)
        else:
            self.log(f"{exchange_name.upper()}: 無支援網路")
            
        self.check_all_workers_done()
        
    def on_query_error(self, exchange_name: str, error_message: str):
        """處理查詢錯誤"""
        self.log(f"{exchange_name.upper()} 錯誤: {error_message}")
        self.check_all_workers_done()
        
    def add_networks_to_table(self, exchange_name: str, networks: List[NetworkInfo]):
        """將網路資訊添加到表格"""
        currency = self.currency_combo.currentText().upper()
        
        for network in networks:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # 填入資料
            self.results_table.setItem(row, 0, QTableWidgetItem(exchange_name.upper()))
            self.results_table.setItem(row, 1, QTableWidgetItem(currency))
            self.results_table.setItem(row, 2, QTableWidgetItem(network.network))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{network.min_withdrawal:.8g}"))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{network.withdrawal_fee:.8g}"))
            
            # 狀態
            status = "正常"
            if not network.deposit_enabled:
                status = "停止入金"
            elif not network.withdrawal_enabled:
                status = "停止出金"
            self.results_table.setItem(row, 5, QTableWidgetItem(status))
            
    def clear_results(self):
        """清空結果表格"""
        self.results_table.setRowCount(0)
        
    def show_progress(self):
        """顯示進度條"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 無限進度條
        
    def hide_progress(self):
        """隱藏進度條"""
        self.progress_bar.setVisible(False)
        
    def check_all_workers_done(self):
        """檢查所有工作執行緒是否完成"""
        active_workers = [w for w in self.workers if w.isRunning()]
        if not active_workers:
            self.hide_progress()
            self.log("查詢完成")
            # 清理完成的工作執行緒
            self.workers = [w for w in self.workers if w.isRunning()]
            
    def log(self, message: str):
        """記錄訊息到日誌"""
        self.log_text.append(f"[{self.get_timestamp()}] {message}")
        
    def get_timestamp(self) -> str:
        """獲取時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
        
    def closeEvent(self, event):
        """視窗關閉事件"""
        # 等待所有工作執行緒完成
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        event.accept()


def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    # 設定應用程式資訊
    app.setApplicationName("Coin Porter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("TerryChengTW")
    
    # 創建主視窗
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())