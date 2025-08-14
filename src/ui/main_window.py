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
from ..core.utils.logger import set_ui_log_callback, log_debug


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
        
        # 設定 logger UI 回呼
        set_ui_log_callback(self.log_without_timestamp)
        
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
        self.enhanced_query_btn = QPushButton("智能幣種識別")
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
        self.enhanced_query_btn.clicked.connect(self.enhanced_query)
        
            
    
    def enhanced_query(self):
        """智能幣種識別 - 直接使用完整數據進行智能分析"""
        currency = self.currency_combo.currentText().upper()
        if not currency:
            self.log("請輸入幣種名稱")
            return
            
        self.log(f"🔍 開始智能識別 {currency}...")
        self.log("🔍 正在從交易所獲取完整數據，這可能需要幾秒...")
        
        self.show_progress()
        self.clear_results()
        
        # 儲存當前幣種
        self.current_enhanced_currency = currency
        
        # 直接啟動智能識別
        self.start_enhanced_identification()
    
    def start_enhanced_identification(self):
        """啟動智能識別部分"""
        # 創建工作器並連接信號
        self.enhanced_worker = EnhancedQueryWorker(self.exchange_manager, self.current_enhanced_currency)
        self.enhanced_worker.finished.connect(self.on_enhanced_query_completed)
        self.enhanced_worker.error.connect(self.on_enhanced_query_error)
        
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
        log_debug("on_enhanced_query_completed 被調用")
        log_debug(f"result: {result}")
        log_debug(f"result type: {type(result)}")
        
        # 快取 searchable 數據供後續使用
        self._cached_searchable_data = searchable_data
        
        self.log("📍 進入智能識別結果處理")
        self.hide_progress()
        
        if not result:
            self.log("❌ 智能識別完成，但無結果")
            return
            
        self.log(f"📊 處理結果: 原始符號={result.original_symbol}")
        
        # 分類顯示查詢結果
        original_currency = result.original_symbol
        traditional_matches = []
        smart_matches = []
        
        for match in result.verified_matches:
            if match.source == "traditional":
                traditional_matches.append(match)
            elif match.source == "smart":
                smart_matches.append(match)
        
        # 顯示傳統查詢結果
        if traditional_matches:
            self.log(f"📋 傳統查詢找到 {len(traditional_matches)} 個匹配")
            for match in traditional_matches:
                self.add_coin_variant_to_table(match, "傳統查詢")
        else:
            self.log("📋 傳統查詢: 無支援網路")
        
        # 顯示智能識別發現的額外匹配
        if smart_matches:
            self.log(f"✨ 智能識別找到 {len(smart_matches)} 個額外的匹配項目")
            for i, match in enumerate(smart_matches):
                self.log(f"  💡 額外發現{i+1}: {match.exchange} - {match.symbol} ({match.network})")
                if match.contract_address:
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
        
    
    def log(self, message: str):
        """記錄訊息到日誌（帶時間戳）"""
        self.log_text.append(f"[{self.get_timestamp()}] {message}")
    
    def log_without_timestamp(self, message: str):
        """記錄訊息到日誌（不帶時間戳，供 logger 回呼使用）"""
        self.log_text.append(f"[{self.get_timestamp()}] {message}")
        
    def get_timestamp(self) -> str:
        """獲取時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
        
    def closeEvent(self, event):
        """視窗關閉事件"""
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