import asyncio
from typing import Dict, List, Optional, Tuple
from .base import BaseExchange, NetworkInfo, ExchangeFactory, RawCoinData, SearchableCoinInfo, SearchableNetworkInfo
from ..config.api_keys import APIKeyManager
from ..config.exchanges_config import ExchangeConfigManager
from ..currency.coin_identifier import CoinIdentifier, CoinIdentificationResult, CoinVariant, NetworkStandardizer
from ..utils.logger import log_info, log_error, log_debug


class ExchangeManager:
    """統一交易所管理器"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager
        self.config_manager = ExchangeConfigManager()
        self._exchanges: Dict[str, BaseExchange] = {}
        self.coin_identifier = CoinIdentifier()
        
        # 動態註冊所有支援的交易所
        self._register_exchanges()
        self._initialize_exchanges()
    
    def _register_exchanges(self):
        """動態註冊交易所類別"""
        for exchange_name in self.config_manager.get_enabled_exchanges():
            exchange_class = self.config_manager.get_exchange_class(exchange_name)
            if exchange_class:
                ExchangeFactory.register(exchange_name, exchange_class)
    
    def _initialize_exchanges(self):
        """初始化已啟用且已配置的交易所"""
        queryable_exchanges = self.api_key_manager.get_queryable_exchanges()
        
        for exchange_name in queryable_exchanges:
            # 為每個交易所使用第一個帳號進行查詢
            account_names = self.api_key_manager.get_exchange_accounts(exchange_name)
            if account_names:
                first_account = account_names[0]
                account_config = self.api_key_manager.get_account(exchange_name, first_account)
                
                if account_config:
                    exchange = ExchangeFactory.create(exchange_name, account_config)
                    self._exchanges[exchange_name] = exchange
    
    
    async def get_all_coins_data(self) -> Tuple[Dict[str, List[RawCoinData]], Dict[str, List[SearchableCoinInfo]]]:
        """一次性獲取所有交易所的完整幣種數據
        
        Returns:
            Tuple[raw_data_by_exchange, searchable_data_by_exchange]: 原始數據和搜索用數據
        """
        log_debug("get_all_coins_data 開始...")
        
        raw_data_by_exchange = {}
        searchable_data_by_exchange = {}
        tasks = []
        exchange_names = []
        
        # 準備所有查詢任務
        for exchange_key, exchange in self._exchanges.items():
            exchange_name = exchange_key.replace('_public', '')
            tasks.append(exchange.get_all_coins_info())
            exchange_names.append(exchange_name)
        
        if not tasks:
            return raw_data_by_exchange, searchable_data_by_exchange
        
        # 並行查詢所有交易所
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                exchange_name = exchange_names[i]
                
                if isinstance(result, Exception):
                    log_error(f"{exchange_name}: {str(result)}")
                    raw_data_by_exchange[exchange_name] = []
                    searchable_data_by_exchange[exchange_name] = []
                else:
                    raw_data, searchable_data = result
                    raw_data_by_exchange[exchange_name] = raw_data
                    searchable_data_by_exchange[exchange_name] = searchable_data
                    log_info(f"{exchange_name}: 獲取 {len(searchable_data)} 個幣種數據")
                    
        except Exception as e:
            log_error(f"查詢所有幣種數據時發生錯誤: {str(e)}")
        
        return raw_data_by_exchange, searchable_data_by_exchange

    async def enhanced_currency_query(self, currency: str) -> Tuple[CoinIdentificationResult, Dict[str, List[SearchableCoinInfo]]]:
        """增強的幣種查詢 - 使用重構後的 CoinIdentifier 統一處理
        
        Args:
            currency: 用戶輸入的幣種符號
            
        Returns:
            CoinIdentificationResult: 包含所有可能匹配的幣種及其網路資訊
        """
        log_debug(f"enhanced_currency_query 開始，幣種: {currency}")
        
        # 一次性獲取所有交易所的完整數據
        log_debug("獲取所有交易所完整數據...")
        raw_data_by_exchange, searchable_data_by_exchange = await self.get_all_coins_data()
        
        # 使用重構後的 CoinIdentifier 統一處理
        log_debug("使用 CoinIdentifier 進行統一識別...")
        identification_result = self.coin_identifier.identify_currency(currency, searchable_data_by_exchange)
        
        log_debug(f"最終結果: {len(identification_result.verified_matches)} 個驗證匹配")
        return identification_result, searchable_data_by_exchange
    
    # 重複的業務邏輯已移動到 CoinIdentifier 中
    # 保持 ExchangeManager 專注於數據獲取和管理功能
    
    def get_available_accounts(self) -> Dict[str, List[str]]:
        """獲取所有可用的帳號
        
        Returns:
            {"binance": ["main", "backup"], "bybit": ["account1"]}
        """
        return self.api_key_manager.get_all_accounts()
    
    def get_exchange_instance(self, exchange_name: str, account_name: str) -> Optional[BaseExchange]:
        """獲取指定交易所和帳號的實例"""
        account_config = self.api_key_manager.get_account(exchange_name, account_name)
        if account_config:
            return ExchangeFactory.create(exchange_name, account_config)
        return None
    
    def is_exchange_available(self, exchange_name: str) -> bool:
        """檢查交易所是否可用（啟用且已配置）"""
        return (
            self.api_key_manager.is_exchange_enabled(exchange_name) and 
            self.api_key_manager.has_exchange_account(exchange_name)
        ) or self.config_manager.supports_public_query(exchange_name)