import sys
import asyncio
from typing import Optional, Dict, List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QSplitter,
    QGroupBox, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot, QObject
from PySide6.QtGui import QFont, QIcon

from ..core.exchanges.manager import ExchangeManager
from ..core.config.api_keys import APIKeyManager
from ..core.config.exchanges_config import ExchangeConfigManager
from ..core.exchanges.base import NetworkInfo
from ..core.currency.coin_identifier import CoinIdentificationResult


class EnhancedQueryWorker(QObject):
    """增強查詢工作器"""
    finished = Signal(object, object)  # CoinIdentificationResult, SearchableCoinInfo數據
    error = Signal(str)  # 錯誤信息
    
    def __init__(self, exchange_manager, currency):
        super().__init__()
        self.exchange_manager = exchange_manager
        self.currency = currency
    
    def run(self):
        """執行查詢"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result, searchable_data = loop.run_until_complete(
                self.exchange_manager.enhanced_currency_query(self.currency)
            )
            
            loop.close()
            self.finished.emit(result, searchable_data)
            
        except Exception as e:
            import traceback
            error_msg = f"智能識別失敗: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)


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
        self.enhanced_query_btn = QPushButton("智能幣種識別")
        control_layout.addWidget(self.query_currencies_btn)
        control_layout.addWidget(self.query_networks_btn)
        control_layout.addWidget(self.enhanced_query_btn)
        
        control_layout.addStretch()
        layout.addWidget(control_group)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 結果顯示
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "交易所", "幣種", "網路", "最小出金", "手續費", "狀態", "合約地址", "類型"
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
        self.enhanced_query_btn.clicked.connect(self.enhanced_query)
        
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
    
    def enhanced_query(self):
        """智能幣種識別 - 先顯示傳統查詢，再顯示智能發現的額外項目"""
        currency = self.currency_combo.currentText().upper()
        if not currency:
            self.log("請輸入幣種名稱")
            return
            
        self.log(f"🔍 開始智能識別 {currency}...")
        self.log("📋 第一步：執行傳統查詢...")
        
        self.show_progress()
        self.clear_results()
        
        # 儲存當前幣種，稍後智能識別會用到
        self.current_enhanced_currency = currency
        
        # 先執行傳統的網路查詢（與 query_networks 相同）
        selected_exchange = self.exchange_combo.currentText()
        if selected_exchange == "所有交易所":
            exchanges = self.config_manager.get_exchange_names()
        else:
            exchanges = [selected_exchange]
        
        self.traditional_results_count = 0
        self.expected_traditional_results = len(exchanges)
        
        # 執行傳統查詢
        for exchange in exchanges:
            worker = QueryWorker(exchange, self.exchange_manager, "networks", currency)
            worker.finished.connect(self.on_traditional_result_for_enhanced)
            worker.error.connect(self.on_query_error)
            self.workers.append(worker)
            worker.start()
    
    def on_traditional_result_for_enhanced(self, exchange_name: str, networks: List[NetworkInfo]):
        """處理傳統查詢結果（用於智能識別流程）"""
        if networks:
            self.log(f"📊 傳統查詢 - {exchange_name.upper()}: 找到 {len(networks)} 個網路")
            self.add_networks_to_table(exchange_name, networks, "傳統查詢")
        else:
            self.log(f"📊 傳統查詢 - {exchange_name.upper()}: 無支援網路")
        
        self.traditional_results_count += 1
        
        # 當所有傳統查詢完成後，啟動智能識別
        if self.traditional_results_count >= self.expected_traditional_results:
            self.log("📋 傳統查詢完成，開始智能識別...")
            self.start_enhanced_identification()
    
    def start_enhanced_identification(self):
        """啟動智能識別部分"""
        # 創建工作器並連接信號
        self.enhanced_worker = EnhancedQueryWorker(self.exchange_manager, self.current_enhanced_currency)
        self.enhanced_worker.finished.connect(self.on_enhanced_query_completed)
        self.enhanced_worker.error.connect(self.on_enhanced_query_error)
        
        # 顯示正在進行的訊息
        self.log("🔍 正在從交易所獲取完整數據，這可能需要幾秒...")
        
        # 使用QTimer在下一個事件循環中啟動
        QTimer.singleShot(0, self.enhanced_worker.run)
    
    @Slot(str)
    def on_enhanced_query_error(self, error_msg: str):
        """處理增強查詢錯誤"""
        self.log(error_msg)
        self.hide_progress()
        self.log("智能識別完成（發生錯誤）")
    
    @Slot(object, object)
    def on_enhanced_query_completed(self, result: CoinIdentificationResult, searchable_data):
        """處理增強查詢結果"""
        print(f"[GUI DEBUG] on_enhanced_query_completed 被調用")
        print(f"[GUI DEBUG] result: {result}")
        print(f"[GUI DEBUG] result type: {type(result)}")
        
        # 快取 searchable 數據供後續使用
        self._cached_searchable_data = searchable_data
        
        self.log("📍 進入智能識別結果處理")
        self.hide_progress()
        
        if not result:
            self.log("❌ 智能識別完成，但無結果")
            return
            
        self.log(f"📊 處理結果: 原始符號={result.original_symbol}")
        
        # 先顯示傳統查詢結果
        self.log("📋 首先顯示傳統查詢結果...")
        
        # 過濾掉已經在傳統查詢中顯示的項目
        additional_matches = []
        original_currency = result.original_symbol
        
        for match in result.verified_matches:
            # 只顯示來源為智能識別且與原始查詢符號不同的匹配
            if match.source == "smart" and match.symbol != original_currency:
                additional_matches.append(match)
        
        # 顯示額外發現的匹配
        if additional_matches:
            self.log(f"✨ 智能識別找到 {len(additional_matches)} 個額外的匹配項目")
            for i, match in enumerate(additional_matches):
                self.log(f"  💡 額外發現{i+1}: {match.exchange} - {match.symbol} ({match.network})")
                self.log(f"      🔗 與 {original_currency} 是同一個代幣（合約: {match.contract_address[:20]}...）")
                self.add_coin_variant_to_table(match, "智能識別")
        else:
            self.log("ℹ️ 智能識別沒有找到額外的匹配項目")
        
        # 顯示可能的匹配  
        if result.possible_matches:
            self.log(f"🤔 找到 {len(result.possible_matches)} 個可能的匹配項目")
            for i, match in enumerate(result.possible_matches):
                self.log(f"  ❓ 可能匹配{i+1}: {match.exchange} - {match.symbol} ({match.network})")
                self.add_coin_variant_to_table(match, "可能匹配")
        
        # 顯示除錯資訊
        if result.debug_info:
            self.log(f"⚠️ 發現 {len(result.debug_info)} 個需要注意的情況")
            for debug in result.debug_info:
                self.log(f"🔍 [警告] {debug}")
        
        self.log("🎉 智能識別完成")
            
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
        
    def add_networks_to_table(self, exchange_name: str, networks: List[NetworkInfo], query_type: str = "傳統查詢"):
        """將網路資訊添加到表格"""
        # 取得幣種名稱，優先使用當前設定的幣種
        if hasattr(self, 'current_enhanced_currency'):
            currency = self.current_enhanced_currency
        else:
            currency = self.currency_combo.currentText().upper()
        
        for network in networks:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # 決定要顯示的幣種符號（優先使用實際符號）
            display_symbol = network.actual_symbol if network.actual_symbol else currency
            
            # 填入資料
            self.results_table.setItem(row, 0, QTableWidgetItem(exchange_name.upper()))
            self.results_table.setItem(row, 1, QTableWidgetItem(display_symbol))
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
            
            # 合約地址和類型
            self.results_table.setItem(row, 6, QTableWidgetItem(network.contract_address or ""))
            self.results_table.setItem(row, 7, QTableWidgetItem(query_type))
    
    def add_coin_variant_to_table(self, variant, match_type: str):
        """將幣種變體添加到表格"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # 填入資料
        self.results_table.setItem(row, 0, QTableWidgetItem(variant.exchange.upper()))
        self.results_table.setItem(row, 1, QTableWidgetItem(variant.symbol))
        self.results_table.setItem(row, 2, QTableWidgetItem(variant.network))
        
        # 嘗試從快取數據獲取真實的手續費、限額和狀態信息
        min_withdrawal, withdrawal_fee, status = self._get_network_details_and_status(variant)
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{min_withdrawal:.8g}" if min_withdrawal is not None else "N/A"))
        self.results_table.setItem(row, 4, QTableWidgetItem(f"{withdrawal_fee:.8g}" if withdrawal_fee is not None else "N/A"))
        
        # 狀態（正常/停止入金/停止出金）
        self.results_table.setItem(row, 5, QTableWidgetItem(status if status else "未知"))
        
        # 合約地址和類型
        self.results_table.setItem(row, 6, QTableWidgetItem(variant.contract_address))
        self.results_table.setItem(row, 7, QTableWidgetItem("智能識別"))
        
    def _get_network_details(self, variant):
        """從快取的搜索數據中獲取網路詳細資訊"""
        # 如果沒有快取數據，返回None
        if not hasattr(self, '_cached_searchable_data') or not self._cached_searchable_data:
            return None, None
            
        exchange_data = self._cached_searchable_data.get(variant.exchange, [])
        
        for coin in exchange_data:
            if coin.symbol == variant.symbol:
                for network in coin.networks:
                    if network.network == variant.network:
                        return network.min_withdrawal, network.withdrawal_fee
                        
        return None, None
        
    def _get_network_details_and_status(self, variant):
        """從快取的搜索數據中獲取網路詳細資訊和狀態"""
        # 如果沒有快取數據，返回None
        if not hasattr(self, '_cached_searchable_data') or not self._cached_searchable_data:
            return None, None, None
            
        exchange_data = self._cached_searchable_data.get(variant.exchange, [])
        
        for coin in exchange_data:
            if coin.symbol == variant.symbol:
                for network in coin.networks:
                    if network.network == variant.network:
                        # 計算狀態（與傳統搜索相同的邏輯）
                        status = "正常"
                        if not network.deposit_enabled:
                            status = "停止入金"
                        elif not network.withdrawal_enabled:
                            status = "停止出金"
                            
                        return network.min_withdrawal, network.withdrawal_fee, status
                        
        return None, None, None
            
    def clear_results(self):
        """清空結果表格"""
        self.results_table.setRowCount(0)
        
    def show_progress(self):
        """顯示進度條"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 無限進度條
        
    @Slot()
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