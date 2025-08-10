import asyncio
from typing import Dict, List, Optional, Tuple
from .base import BaseExchange, NetworkInfo, ExchangeFactory
from .binance import BinanceExchange
from .bybit import BybitExchange  
from .bitget import BitgetExchange
from ..config.api_keys import APIKeyManager


class ExchangeManager:
    """統一交易所管理器"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager
        self._exchanges: Dict[str, BaseExchange] = {}
        
        # 註冊所有支援的交易所
        ExchangeFactory.register("binance", BinanceExchange)
        ExchangeFactory.register("bybit", BybitExchange)
        ExchangeFactory.register("bitget", BitgetExchange)
        
        self._initialize_exchanges()
    
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
    
    def _initialize_public_exchanges(self):
        """初始化公開查詢的交易所（不需認證）"""
        enabled_exchanges = self.api_key_manager.get_enabled_exchanges()
        
        for exchange_name in enabled_exchanges:
            if exchange_name not in self._exchanges:
                # 對於支援公開查詢的交易所（如 Bitget），創建無認證實例
                if exchange_name == "bitget":
                    exchange = ExchangeFactory.create(exchange_name, None)
                    self._exchanges[f"{exchange_name}_public"] = exchange
    
    async def query_currency_support(self, currency: str) -> Dict[str, List[NetworkInfo]]:
        """查詢所有交易所對指定幣種的支援情況
        
        Returns:
            {"binance": [NetworkInfo(...), ...], "bybit": [...]}
        """
        # 確保公開查詢的交易所也被初始化
        self._initialize_public_exchanges()
        
        results = {}
        tasks = []
        exchange_names = []
        
        # 準備所有查詢任務
        for exchange_key, exchange in self._exchanges.items():
            exchange_name = exchange_key.replace('_public', '')
            tasks.append(exchange.get_currency_networks(currency))
            exchange_names.append(exchange_name)
        
        if not tasks:
            return results
        
        # 並行查詢所有交易所
        try:
            network_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(network_results):
                exchange_name = exchange_names[i]
                
                if isinstance(result, Exception):
                    print(f"[錯誤] {exchange_name}: {str(result)}")
                    results[exchange_name] = []
                else:
                    results[exchange_name] = result
                    
        except Exception as e:
            print(f"[錯誤] 查詢幣種支援時發生錯誤: {str(e)}")
        
        return results
    
    async def get_all_supported_currencies(self) -> Dict[str, List[str]]:
        """獲取所有交易所支援的幣種列表
        
        Returns:
            {"binance": ["BTC", "ETH", ...], "bybit": [...]}
        """
        self._initialize_public_exchanges()
        
        results = {}
        tasks = []
        exchange_names = []
        
        # 準備所有查詢任務
        for exchange_key, exchange in self._exchanges.items():
            exchange_name = exchange_key.replace('_public', '')
            tasks.append(exchange.get_supported_currencies())
            exchange_names.append(exchange_name)
        
        if not tasks:
            return results
        
        # 並行查詢所有交易所
        try:
            currency_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(currency_results):
                exchange_name = exchange_names[i]
                
                if isinstance(result, Exception):
                    print(f"[錯誤] {exchange_name}: {str(result)}")
                    results[exchange_name] = []
                else:
                    results[exchange_name] = result
                    
        except Exception as e:
            print(f"[錯誤] 查詢支援幣種時發生錯誤: {str(e)}")
        
        return results
    
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
        ) or (exchange_name == "bitget")  # Bitget 支援公開查詢