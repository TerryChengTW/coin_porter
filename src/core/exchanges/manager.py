import asyncio
from typing import Dict, List, Optional, Tuple
from .base import BaseExchange, NetworkInfo, ExchangeFactory, RawCoinData, SearchableCoinInfo, SearchableNetworkInfo
from ..config.api_keys import APIKeyManager
from ..config.exchanges_config import ExchangeConfigManager
from ..currency.coin_identifier import CoinIdentifier, CoinIdentificationResult, CoinVariant, NetworkStandardizer


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
        print(f"[DEBUG] get_all_coins_data 開始...")
        
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
                    print(f"[錯誤] {exchange_name}: {str(result)}")
                    raw_data_by_exchange[exchange_name] = []
                    searchable_data_by_exchange[exchange_name] = []
                else:
                    raw_data, searchable_data = result
                    raw_data_by_exchange[exchange_name] = raw_data
                    searchable_data_by_exchange[exchange_name] = searchable_data
                    print(f"[成功] {exchange_name}: 獲取 {len(searchable_data)} 個幣種數據")
                    
        except Exception as e:
            print(f"[錯誤] 查詢所有幣種數據時發生錯誤: {str(e)}")
        
        return raw_data_by_exchange, searchable_data_by_exchange

    async def enhanced_currency_query(self, currency: str) -> Tuple[CoinIdentificationResult, Dict[str, List[SearchableCoinInfo]]]:
        """增強的幣種查詢 - 使用雙路線識別策略，避免重複API呼叫
        
        Args:
            currency: 用戶輸入的幣種符號
            
        Returns:
            CoinIdentificationResult: 包含所有可能匹配的幣種及其網路資訊
        """
        print(f"[DEBUG] enhanced_currency_query 開始，幣種: {currency}")
        
        # 一次性獲取所有交易所的完整數據
        print(f"[DEBUG] 獲取所有交易所完整數據...")
        raw_data_by_exchange, searchable_data_by_exchange = await self.get_all_coins_data()
        
        # 從 searchable 數據中執行傳統查詢
        print(f"[DEBUG] 從完整數據中執行傳統查詢...")
        traditional_results = self._search_from_cached_data(currency, searchable_data_by_exchange)
        print(f"[DEBUG] 傳統查詢結果: {traditional_results}")
        
        # 執行智能識別（基於合約地址的跨交易所識別）
        print(f"[DEBUG] 執行智能識別...")
        smart_results = self._smart_identification_from_cached_data(currency, searchable_data_by_exchange)
        print(f"[DEBUG] 智能識別結果: {len(smart_results)} 個匹配")
        
        # 合併結果
        all_matches = []
        all_matches.extend(self._convert_traditional_to_variants(traditional_results, currency))
        all_matches.extend(smart_results)
        
        # 去重（使用更寬鬆的鍵，避免合約地址空字串導致的問題）
        seen = set()
        verified_matches = []
        for match in all_matches:
            # 對於去重，如果沒有合約地址，不使用合約地址作為去重鍵的一部分
            if match.contract_address and match.contract_address.strip():
                key = (match.exchange, match.symbol, match.network, match.contract_address.lower())
            else:
                key = (match.exchange, match.symbol, match.network)
            
            if key not in seen:
                seen.add(key)
                verified_matches.append(match)
        
        identification_result = CoinIdentificationResult(
            original_symbol=currency,
            verified_matches=verified_matches,
            possible_matches=[],
            debug_info=[]
        )
        
        print(f"[DEBUG] 最終結果: {len(verified_matches)} 個驗證匹配")
        return identification_result, searchable_data_by_exchange
    
    def _search_from_cached_data(self, currency: str, searchable_data: Dict[str, List[SearchableCoinInfo]]) -> Dict[str, List[NetworkInfo]]:
        """從快取的 searchable 數據中搜索特定幣種（傳統查詢）"""
        results = {}
        
        for exchange_name, coins in searchable_data.items():
            networks = []
            for coin in coins:
                # 檢查是否匹配：直接匹配或去除 denomination 後匹配
                symbol_matches = False
                
                # 直接匹配
                if coin.symbol.upper() == currency.upper():
                    symbol_matches = True
                
                # 檢查 denomination 匹配 (處理 1000SATS -> SATS, 1MBABYDOGE -> BABYDOGE 的情況)
                elif coin.denomination and coin.denomination > 1:
                    # 如果幣種符號以 denomination 數字開頭，去掉前綴比較
                    if coin.symbol.startswith(str(coin.denomination)):
                        base_symbol = coin.symbol[len(str(coin.denomination)):]
                        if base_symbol.upper() == currency.upper():
                            symbol_matches = True
                    # 處理簡寫格式 (1M = 1,000,000)
                    elif coin.denomination == 1000000 and coin.symbol.startswith('1M'):
                        base_symbol = coin.symbol[2:]  # 去掉 "1M"
                        if base_symbol.upper() == currency.upper():
                            symbol_matches = True
                
                if symbol_matches:
                    # 轉換 SearchableNetworkInfo 為 NetworkInfo
                    for searchable_net in coin.networks:
                        network_info = NetworkInfo(
                            network=searchable_net.network,
                            min_withdrawal=searchable_net.min_withdrawal,
                            withdrawal_fee=searchable_net.withdrawal_fee,
                            deposit_enabled=searchable_net.deposit_enabled,
                            withdrawal_enabled=searchable_net.withdrawal_enabled,
                            contract_address=searchable_net.contract_address,
                            network_full_name=searchable_net.chain_type or searchable_net.network,
                            browser_url=searchable_net.browser_url,
                            actual_symbol=coin.symbol  # 設定實際找到的符號
                        )
                        networks.append(network_info)
                    break
            results[exchange_name] = networks
        
        return results
    
    def _smart_identification_from_cached_data(self, currency: str, searchable_data: Dict[str, List[SearchableCoinInfo]]) -> List[CoinVariant]:
        """從快取數據執行智能識別（基於合約地址的跨交易所匹配），排除傳統查詢已找到的項目"""
        contract_map = {}  # {standardized_contract_key: [(exchange, symbol, original_network)]}
        variants = []
        network_standardizer = NetworkStandardizer()
        
        # 首先獲取傳統查詢的結果，用於過濾重複項
        traditional_found = set()  # (exchange, symbol, network)
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                # 檢查是否匹配：直接匹配或去除 denomination 後匹配
                symbol_matches = False
                
                # 直接匹配
                if coin.symbol.upper() == currency.upper():
                    symbol_matches = True
                
                # 檢查 denomination 匹配 (處理 1000SATS -> SATS, 1MBABYDOGE -> BABYDOGE 的情況)
                elif coin.denomination and coin.denomination > 1:
                    # 如果幣種符號以 denomination 數字開頭，去掉前綴比較
                    if coin.symbol.startswith(str(coin.denomination)):
                        base_symbol = coin.symbol[len(str(coin.denomination)):]
                        if base_symbol.upper() == currency.upper():
                            symbol_matches = True
                    # 處理簡寫格式 (1M = 1,000,000)
                    elif coin.denomination == 1000000 and coin.symbol.startswith('1M'):
                        base_symbol = coin.symbol[2:]  # 去掉 "1M"
                        if base_symbol.upper() == currency.upper():
                            symbol_matches = True
                
                if symbol_matches:
                    for network in coin.networks:
                        traditional_found.add((exchange_name, coin.symbol, network.network))
        
        print(f"[DEBUG] 智能識別：傳統查詢已找到 {len(traditional_found)} 個項目")
        
        # 收集所有合約地址映射（使用標準化網路名稱）
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                for network in coin.networks:
                    if network.contract_address:
                        # 使用標準化網路名稱
                        std_network = network_standardizer.standardize_network(network.network)
                        contract_key = f"{network.contract_address.lower()}_{std_network}"
                        if contract_key not in contract_map:
                            contract_map[contract_key] = []
                        contract_map[contract_key].append((exchange_name, coin.symbol, network.network))
        
        print(f"[DEBUG] 智能識別：收集到 {len(contract_map)} 個標準化合約地址映射")
        
        # 找出與輸入幣種相關的合約地址（使用標準化網路）
        input_contracts = set()
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                # 檢查所有可能匹配的符號（包括 denomination 處理）
                symbol_matches = False
                
                if coin.symbol.upper() == currency.upper():
                    symbol_matches = True
                elif coin.denomination and coin.denomination > 1:
                    if coin.symbol.startswith(str(coin.denomination)):
                        base_symbol = coin.symbol[len(str(coin.denomination)):]
                        if base_symbol.upper() == currency.upper():
                            symbol_matches = True
                    elif coin.denomination == 1000000 and coin.symbol.startswith('1M'):
                        base_symbol = coin.symbol[2:]
                        if base_symbol.upper() == currency.upper():
                            symbol_matches = True
                
                if symbol_matches:
                    for network in coin.networks:
                        if network.contract_address:
                            std_network = network_standardizer.standardize_network(network.network)
                            contract_key = f"{network.contract_address.lower()}_{std_network}"
                            input_contracts.add(contract_key)
                            print(f"[DEBUG] 找到 {currency} 的標準化合約: {contract_key} ({exchange_name}, 原始網路: {network.network})")
        
        print(f"[DEBUG] {currency} 相關的標準化合約地址: {len(input_contracts)} 個")
        
        # 第一階段：找出所有使用相同合約地址的幣種
        related_symbols = set()
        for contract_key in input_contracts:
            if contract_key in contract_map:
                entries = contract_map[contract_key]
                print(f"[DEBUG] 標準化合約 {contract_key} 有 {len(entries)} 個變體: {entries}")
                for exchange, symbol, original_network in entries:
                    related_symbols.add(symbol.upper())
        
        print(f"[DEBUG] 找到 {len(related_symbols)} 個相關幣種符號: {related_symbols}")
        
        # 第二階段：獲取所有相關幣種的所有網路（包括原本沒有的網路）
        all_related_contracts = set()
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                if coin.symbol.upper() in related_symbols:
                    for network in coin.networks:
                        if network.contract_address:
                            std_network = network_standardizer.standardize_network(network.network)
                            contract_key = f"{network.contract_address.lower()}_{std_network}"
                            all_related_contracts.add(contract_key)
                            print(f"[DEBUG] 擴展搜索：找到 {coin.symbol} 的合約: {contract_key} ({exchange_name}, 網路: {network.network})")
        
        print(f"[DEBUG] 擴展後總共有 {len(all_related_contracts)} 個相關合約地址")
        
        # 第三階段：返回所有相關合約的所有變體（排除傳統查詢已找到的）
        for contract_key in all_related_contracts:
            if contract_key in contract_map:
                entries = contract_map[contract_key]
                # 包含所有使用相同合約的幣種，但排除傳統查詢已找到的
                for exchange, symbol, original_network in entries:
                    # 檢查是否已被傳統查詢找到
                    if (exchange, symbol, original_network) not in traditional_found:
                        variants.append(CoinVariant(
                            exchange=exchange,
                            symbol=symbol,
                            network=original_network,  # 使用原始網路名稱
                            contract_address=contract_key.split('_')[0],  # 取出合約地址部分
                            is_verified=True,
                            source="smart"
                        ))
        
        print(f"[DEBUG] 智能識別最終找到 {len(variants)} 個額外變體（排除重複）")
        return variants
    
    def _convert_traditional_to_variants(self, traditional_results: Dict[str, List[NetworkInfo]], currency: str) -> List[CoinVariant]:
        """將傳統查詢結果轉換為 CoinVariant 格式"""
        variants = []
        
        for exchange_name, networks in traditional_results.items():
            for network in networks:
                # 使用實際找到的符號，如果沒有則使用查詢符號
                actual_symbol = network.actual_symbol if network.actual_symbol else currency.upper()
                variants.append(CoinVariant(
                    exchange=exchange_name,
                    symbol=actual_symbol,
                    network=network.network,
                    contract_address=network.contract_address or "",
                    is_verified=True,
                    source="traditional"
                ))
        
        return variants
    
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