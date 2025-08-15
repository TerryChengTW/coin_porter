import sys
import asyncio
from typing import Optional, Dict, List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QSplitter,
    QGroupBox, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QAbstractItemView, QAbstractButton
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot, QObject
from PySide6.QtGui import QFont, QIcon, QKeySequence, QClipboard

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
    
    def __init__(self, exchange_manager, currency, selected_exchanges=None):
        super().__init__()
        self.exchange_manager = exchange_manager
        self.currency = currency
        self.selected_exchanges = selected_exchanges
    
    def run(self):
        """執行查詢"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result, searchable_data = loop.run_until_complete(
                self.exchange_manager.enhanced_currency_query(self.currency, self.selected_exchanges)
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
        
        # 初始化排序相關變數
        self.original_data = []  # 儲存原始資料順序
        self.sort_states = {}  # 每欄的排序狀態 (0=原始, 1=升序, 2=降序)
        self.pending_variants = []  # 暫存變體數據供統一格式化
        
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
        exchange_group = QGroupBox("交易所選擇")
        exchange_layout = QVBoxLayout(exchange_group)
        
        # 全選勾選框（只顯示勾選框，不顯示文字）
        self.select_all_checkbox = QCheckBox()
        self.select_all_checkbox.setChecked(True)  # 預設全選
        self.select_all_checkbox.clicked.connect(self.on_select_all_clicked)
        exchange_layout.addWidget(self.select_all_checkbox)
        
        # 個別交易所勾選框，三個一排
        self.exchange_checkboxes = {}
        exchange_names = self.config_manager.get_exchange_names()
        
        # 創建水平佈局來放置三個勾選框
        exchanges_row_layout = QHBoxLayout()
        
        for i, exchange_name in enumerate(exchange_names):
            checkbox = QCheckBox(exchange_name.upper())
            checkbox.setChecked(True)  # 預設全選
            checkbox.clicked.connect(self.on_exchange_checkbox_clicked)
            self.exchange_checkboxes[exchange_name] = checkbox
            exchanges_row_layout.addWidget(checkbox)
        
        # 添加彈性空間，讓勾選框向左對齊
        exchanges_row_layout.addStretch()
        
        exchange_layout.addLayout(exchanges_row_layout)
        control_layout.addWidget(exchange_group)
        
        # 幣種輸入
        control_layout.addWidget(QLabel("幣種:"))
        self.currency_combo = QComboBox()
        self.currency_combo.setEditable(True)
        self.currency_combo.addItems(["BTC", "ETH", "USDT", "USDC"])
        control_layout.addWidget(self.currency_combo)
        
        # 查詢按鈕
        self.enhanced_query_btn = QPushButton("智能幣種識別")
        control_layout.addWidget(self.enhanced_query_btn)
        
        # 模擬數據按鈕（用於測試排序功能）
        self.mock_data_btn = QPushButton("加載模擬數據")
        control_layout.addWidget(self.mock_data_btn)
        
        
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
        
        # 設定表格選擇模式，支援多選
        self.results_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        
        # 設定表格樣式和排序
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.sectionClicked.connect(self.on_header_clicked)
        
        # 啟用表格左上角按鈕，支援全選
        self.results_table.setCornerButtonEnabled(True)
        
        # 連接左上角按鈕的點擊事件到全選功能
        # 使用 QTimer.singleShot 確保在 UI 初始化後再連接信號
        QTimer.singleShot(0, self.connect_corner_button)
        
        # 初始化每欄的排序狀態為原始狀態(0)
        for i in range(8):
            self.sort_states[i] = 0
        
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
        self.mock_data_btn.clicked.connect(self.load_mock_data)
    
    def on_select_all_clicked(self):
        """處理全選勾選框點擊"""
        is_checked = self.select_all_checkbox.isChecked()
        
        # 設定所有交易所勾選框的狀態
        for checkbox in self.exchange_checkboxes.values():
            checkbox.setChecked(is_checked)
    
    def on_exchange_checkbox_clicked(self):
        """處理個別交易所勾選框點擊"""
        # 檢查是否所有交易所都被選中
        all_checked = all(checkbox.isChecked() for checkbox in self.exchange_checkboxes.values())
        any_checked = any(checkbox.isChecked() for checkbox in self.exchange_checkboxes.values())
        
        # 更新全選勾選框的狀態
        if all_checked:
            self.select_all_checkbox.setChecked(True)
        else:
            self.select_all_checkbox.setChecked(False)
        
            
    
    def enhanced_query(self):
        """智能幣種識別 - 直接使用完整數據進行智能分析"""
        currency = self.currency_combo.currentText().upper()
        if not currency:
            self.log("請輸入幣種名稱")
            return
        
        # 獲取選中的交易所
        selected_exchanges = []
        for exchange_name, checkbox in self.exchange_checkboxes.items():
            if checkbox.isChecked():
                selected_exchanges.append(exchange_name)
        
        if not selected_exchanges:
            self.log("請至少選擇一個交易所")
            return
            
        if len(selected_exchanges) == len(self.config_manager.get_exchange_names()):
            self.log(f"🔍 開始智能識別 {currency} (所有交易所)...")
        else:
            self.log(f"🔍 開始智能識別 {currency} ({', '.join(sorted(selected_exchanges))})...")
        self.log("🔍 正在從交易所獲取完整數據，這可能需要幾秒...")
        
        self.show_progress()
        self.clear_results()
        
        # 儲存當前幣種和選中的交易所
        self.current_enhanced_currency = currency
        self.current_selected_exchanges = set(selected_exchanges)
        
        # 直接啟動智能識別
        self.start_enhanced_identification()
    
    def start_enhanced_identification(self):
        """啟動智能識別部分"""
        # 創建工作器並連接信號
        self.enhanced_worker = EnhancedQueryWorker(self.exchange_manager, self.current_enhanced_currency, self.current_selected_exchanges)
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
        
        # 清空暫存的變體數據
        self.pending_variants = []
        
        # 分類顯示查詢結果
        original_currency = result.original_symbol
        traditional_matches = []
        smart_matches = []
        
        for match in result.verified_matches:
            if match.source == "traditional":
                traditional_matches.append(match)
            elif match.source == "smart":
                smart_matches.append(match)
        
        # 收集傳統查詢結果
        if traditional_matches:
            self.log(f"📋 傳統查詢找到 {len(traditional_matches)} 個匹配")
            for match in traditional_matches:
                self.add_coin_variant_to_table(match, "傳統查詢")
        else:
            self.log("📋 傳統查詢: 無支援網路")
        
        # 收集智能識別發現的額外匹配
        if smart_matches:
            self.log(f"✨ 智能識別找到 {len(smart_matches)} 個額外的匹配項目")
            for i, match in enumerate(smart_matches):
                self.log(f"  💡 額外發現{i+1}: {match.exchange} - {match.symbol} ({match.network})")
                if match.contract_address:
                    self.log(f"      🔗 與 {original_currency} 是同一個代幣（合約: {match.contract_address[:20]}...）")
                self.add_coin_variant_to_table(match, "智能識別")
        else:
            self.log("ℹ️ 智能識別沒有找到額外的匹配項目")
        
        # 收集可能的匹配  
        if result.possible_matches:
            self.log(f"🤔 找到 {len(result.possible_matches)} 個可能的匹配項目")
            for i, match in enumerate(result.possible_matches):
                self.log(f"  ❓ 可能匹配{i+1}: {match.exchange} - {match.symbol} ({match.network})")
                self.add_coin_variant_to_table(match, "可能匹配")
        
        # 統一格式化並添加到表格
        self.finalize_variants_to_table()
        
        # 顯示除錯資訊
        if result.debug_info:
            self.log(f"⚠️ 發現 {len(result.debug_info)} 個需要注意的情況")
            for debug in result.debug_info:
                self.log(f"🔍 [警告] {debug}")
        
        self.log("🎉 智能識別完成")
    
    def load_mock_data(self):
        """加載模擬數據用於測試排序功能"""
        self.log("📂 加載模擬數據...")
        self.clear_results()
        
        # 模擬數據
        mock_data = [
            ["BINANCE", "BTC", "BTC", "0.001", "0.0005", "正常", "", "模擬數據"],
            ["BYBIT", "BTC", "BTC", "0.002", "0.0003", "正常", "", "模擬數據"],
            ["BITGET", "BTC", "Bitcoin", "0.0015", "0.0004", "停止入金", "", "模擬數據"],
            ["BINANCE", "ETH", "ETH", "0.01", "0.005", "正常", "0x123...abc", "模擬數據"],
            ["BYBIT", "ETH", "ERC20", "0.02", "0.003", "正常", "0x123...abc", "模擬數據"],
            ["BITGET", "ETH", "Ethereum", "0.015", "0.004", "停止出金", "0x123...abc", "模擬數據"],
            ["BINANCE", "USDT", "TRC20", "10", "1", "正常", "TR7...123", "模擬數據"],
            ["BYBIT", "USDT", "ERC20", "20", "5", "正常", "0xdAC...321", "模擬數據"],
            ["BITGET", "USDT", "BSC", "5", "0.8", "正常", "0x55d...456", "模擬數據"],
            ["BINANCE", "USDC", "ERC20", "10", "5", "正常", "0xA0b...789", "模擬數據"],
        ]
        
        # 將模擬數據添加到表格
        for row_data in mock_data:
            # 儲存原始資料
            self.original_data.append(row_data)
            
            # 添加到表格
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            for col, value in enumerate(row_data):
                self.results_table.setItem(row, col, QTableWidgetItem(str(value)))
        
        self.log(f"✅ 已加載 {len(mock_data)} 筆模擬數據，可點擊表格標題測試排序功能")
            
        
        
    
    def add_networks_to_table(self, exchange_name: str, networks: List[NetworkInfo], query_type: str = "傳統查詢"):
        """將網路資訊添加到表格"""
        # 取得幣種名稱，優先使用當前設定的幣種
        if hasattr(self, 'current_enhanced_currency'):
            currency = self.current_enhanced_currency
        else:
            currency = self.currency_combo.currentText().upper()
        
        # 先收集所有數據
        networks_data = []
        min_withdrawals = []
        withdrawal_fees = []
        
        for network in networks:
            # 決定要顯示的幣種符號（優先使用實際符號）
            display_symbol = network.actual_symbol if network.actual_symbol else currency
            
            # 狀態
            status = "正常"
            if not network.deposit_enabled:
                status = "停止入金"
            elif not network.withdrawal_enabled:
                status = "停止出金"
            
            networks_data.append({
                'exchange': exchange_name.upper(),
                'symbol': display_symbol,
                'network': network.network,
                'min_withdrawal': network.min_withdrawal,
                'withdrawal_fee': network.withdrawal_fee,
                'status': status,
                'contract_address': network.contract_address or "",
                'type': query_type
            })
            
            min_withdrawals.append(network.min_withdrawal)
            withdrawal_fees.append(network.withdrawal_fee)
        
        # 對齊格式化數字
        aligned_min_withdrawals = self.align_decimal_numbers(min_withdrawals)
        aligned_withdrawal_fees = self.align_decimal_numbers(withdrawal_fees)
        
        # 添加到表格
        for i, network_data in enumerate(networks_data):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # 準備資料
            row_data = [
                network_data['exchange'],
                network_data['symbol'],
                network_data['network'],
                aligned_min_withdrawals[i],
                aligned_withdrawal_fees[i],
                network_data['status'],
                network_data['contract_address'],
                network_data['type']
            ]
            
            # 儲存原始資料
            self.original_data.append(row_data)
            
            # 填入表格
            for col, value in enumerate(row_data):
                self.results_table.setItem(row, col, QTableWidgetItem(str(value)))
    
    def add_coin_variant_to_table(self, variant, match_type: str):
        """將幣種變體添加到表格"""
        # 嘗試從快取數據獲取真實的手續費、限額和狀態信息
        min_withdrawal, withdrawal_fee, status = self._get_network_details_and_status(variant)
        
        # 收集數據供統一格式化
        self.pending_variants.append({
            'variant': variant,
            'match_type': match_type,
            'min_withdrawal': min_withdrawal,
            'withdrawal_fee': withdrawal_fee,
            'status': status if status else "未知"
        })
    
    def finalize_variants_to_table(self):
        """統一格式化所有變體數據並添加到表格"""
        if not self.pending_variants:
            return
        
        # 收集所有最小出金和手續費數據
        min_withdrawals = []
        withdrawal_fees = []
        
        for variant_data in self.pending_variants:
            min_withdrawals.append(variant_data['min_withdrawal'])
            withdrawal_fees.append(variant_data['withdrawal_fee'])
        
        # 統一對齊格式化
        aligned_min_withdrawals = self.align_decimal_numbers(min_withdrawals)
        aligned_withdrawal_fees = self.align_decimal_numbers(withdrawal_fees)
        
        # 添加到表格
        for i, variant_data in enumerate(self.pending_variants):
            variant = variant_data['variant']
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # 準備資料
            row_data = [
                variant.exchange.upper(),
                variant.symbol,
                variant.network,
                aligned_min_withdrawals[i],
                aligned_withdrawal_fees[i],
                variant_data['status'],
                variant.contract_address or "",
                variant_data['match_type']
            ]
            
            # 儲存原始資料
            self.original_data.append(row_data)
            
            # 填入表格
            for col, value in enumerate(row_data):
                self.results_table.setItem(row, col, QTableWidgetItem(str(value)))
        
        # 清空暫存數據
        self.pending_variants = []
        
        
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
            
    def on_header_clicked(self, logical_index):
        """處理表格標題欄位點擊，實現三種排序狀態循環"""
        # 獲取當前欄位的排序狀態
        current_state = self.sort_states[logical_index]
        
        # 重置其他欄位的排序狀態為原始狀態
        for i in range(8):
            if i != logical_index:
                self.sort_states[i] = 0
        
        # 循環切換當前欄位的排序狀態：原始(0) -> 升序(1) -> 降序(2) -> 原始(0)
        new_state = (current_state + 1) % 3
        self.sort_states[logical_index] = new_state
        
        # 更新表格標題顯示排序狀態
        self.update_header_labels()
        
        # 根據新狀態進行排序
        if new_state == 0:
            # 恢復原始順序
            self.restore_original_order()
        elif new_state == 1:
            # 升序排序
            self.results_table.sortItems(logical_index, Qt.AscendingOrder)
        else:
            # 降序排序
            self.results_table.sortItems(logical_index, Qt.DescendingOrder)
    
    def update_header_labels(self):
        """更新表格標題，顯示當前排序狀態"""
        original_labels = ["交易所", "幣種", "網路", "最小出金", "手續費", "狀態", "合約地址", "類型"]
        
        for i, label in enumerate(original_labels):
            if self.sort_states[i] == 1:
                # 升序
                new_label = f"{label} ↑"
            elif self.sort_states[i] == 2:
                # 降序
                new_label = f"{label} ↓"
            else:
                # 原始狀態
                new_label = label
            
            self.results_table.setHorizontalHeaderItem(i, QTableWidgetItem(new_label))
    
    def restore_original_order(self):
        """恢復表格的原始資料順序"""
        if not self.original_data:
            return
            
        # 清空表格
        self.results_table.setRowCount(0)
        
        # 按原始順序重新填入資料
        for row_data in self.original_data:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            for col, value in enumerate(row_data):
                self.results_table.setItem(row, col, QTableWidgetItem(str(value)))
    
    def clear_results(self):
        """清空結果表格"""
        self.results_table.setRowCount(0)
        self.original_data.clear()  # 同時清空原始資料
        self.pending_variants.clear()  # 清空暫存的變體數據
        # 重置所有欄位的排序狀態
        for i in range(8):
            self.sort_states[i] = 0
        # 重置表格標題
        self.update_header_labels()
        
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
        
    def connect_corner_button(self):
        """連接表格左上角按鈕的點擊事件"""
        # 尋找表格的 corner button
        def find_corner_button(widget):
            for child in widget.findChildren(QAbstractButton):
                # corner button 通常沒有文字且大小較小
                if not child.text() and child.size().width() < 50:
                    return child
            return None
        
        corner_button = find_corner_button(self.results_table)
        if corner_button:
            corner_button.clicked.connect(self.on_corner_button_clicked)
    
    def on_corner_button_clicked(self):
        """處理表格左上角按鈕點擊"""
        self.select_all_table()
    
    def select_all_table(self):
        """全選表格內容"""
        if self.results_table.rowCount() > 0:
            self.results_table.selectAll()
            self.log(f"已全選表格 {self.results_table.rowCount()} 行內容")
        else:
            self.log("表格無內容可選")
    
    def get_timestamp(self) -> str:
        """獲取時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def format_decimal_number(self, value) -> str:
        """將科學記號轉換為普通小數格式"""
        if value is None:
            return "N/A"
        
        # 轉換為float以處理字符串格式的科學記號
        try:
            if isinstance(value, str):
                float_value = float(value)
            else:
                float_value = float(value)
        except (ValueError, TypeError):
            return str(value)
        
        # 如果值為0，直接返回"0"
        if float_value == 0:
            return "0"
        
        # 使用 Decimal 來精確處理小數位數
        from decimal import Decimal, getcontext
        getcontext().prec = 50  # 設定精度
        
        # 轉換為 Decimal 來避免浮點數精度問題
        decimal_value = Decimal(str(float_value))
        
        # 轉換為字符串並去掉尾隨的零
        formatted = f"{decimal_value:.20f}".rstrip('0').rstrip('.')
        
        return formatted
    
    def align_decimal_numbers(self, values: list) -> list:
        """對齊小數點位數顯示，找出所有數字中最多的小數位數並統一格式"""
        if not values:
            return []
        
        # 先轉換所有值為普通小數格式
        formatted_values = []
        max_decimal_places = 0
        
        for value in values:
            formatted = self.format_decimal_number(value)
            formatted_values.append(formatted)
            
            # 計算所有有效數字的小數位數（包括0）
            if formatted != "N/A":
                if '.' in formatted:
                    decimal_places = len(formatted.split('.')[1])
                    max_decimal_places = max(max_decimal_places, decimal_places)
        
        # 統一小數位數顯示
        aligned_values = []
        for formatted in formatted_values:
            if formatted == "N/A":
                aligned_values.append(formatted)
            elif '.' not in formatted:
                # 沒有小數點的數字（包括整數和0）
                if max_decimal_places > 0:
                    aligned_values.append(f"{formatted}.{'0' * max_decimal_places}")
                else:
                    aligned_values.append(formatted)
            else:
                # 已經有小數點，補齊位數到最大位數
                current_decimal_places = len(formatted.split('.')[1])
                if current_decimal_places < max_decimal_places:
                    zeros_to_add = max_decimal_places - current_decimal_places
                    aligned_values.append(f"{formatted}{'0' * zeros_to_add}")
                else:
                    aligned_values.append(formatted)
        
        return aligned_values
    
    
    def copy_selected_cells(self):
        """複製選中的表格內容到剪貼簿"""
        selected_ranges = self.results_table.selectedRanges()
        if not selected_ranges:
            return
        
        # 收集所有選中的儲存格
        selected_cells = []
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.results_table.item(row, col)
                    cell_text = item.text() if item else ""
                    selected_cells.append((row, col, cell_text))
        
        if not selected_cells:
            return
        
        # 按行列排序
        selected_cells.sort(key=lambda x: (x[0], x[1]))
        
        # 轉換為表格格式
        if len(selected_cells) == 1:
            # 單個儲存格
            clipboard_text = selected_cells[0][2]
        else:
            # 多個儲存格，構建表格格式
            rows_data = {}
            for row, col, text in selected_cells:
                if row not in rows_data:
                    rows_data[row] = {}
                rows_data[row][col] = text
            
            # 構建文字格式（用tab分隔列，用換行分隔行）
            clipboard_lines = []
            for row in sorted(rows_data.keys()):
                row_data = rows_data[row]
                if len(row_data) == 1:
                    # 單列資料
                    clipboard_lines.append(list(row_data.values())[0])
                else:
                    # 多列資料，用tab分隔
                    min_col = min(row_data.keys())
                    max_col = max(row_data.keys())
                    row_cells = []
                    for col in range(min_col, max_col + 1):
                        row_cells.append(row_data.get(col, ""))
                    clipboard_lines.append("\t".join(row_cells))
            
            clipboard_text = "\n".join(clipboard_lines)
        
        # 複製到剪貼簿
        clipboard = QApplication.clipboard()
        clipboard.setText(clipboard_text)
        
        # 記錄到日誌
        selected_count = len(selected_cells)
        if selected_count == 1:
            self.log(f"已複製 1 個儲存格")
        else:
            self.log(f"已複製 {selected_count} 個儲存格")
    
    def keyPressEvent(self, event):
        """處理鍵盤事件"""
        # 檢查是否按下 Ctrl+C
        if event.matches(QKeySequence.Copy):
            # 如果焦點在表格上，執行自定義複製
            if self.results_table.hasFocus():
                self.copy_selected_cells()
                return
        
        
        # 其他按鍵交給父類處理
        super().keyPressEvent(event)
    
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