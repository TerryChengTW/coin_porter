"""
幣種識別與網路標準化模組
提供跨交易所的幣種智能識別和網路名稱標準化功能
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

# 導入必要的數據結構
# 注意：這裡使用相對導入來避免循環依賴
if __name__ != '__main__':
    from ..exchanges.base import NetworkInfo, SearchableCoinInfo, SearchableNetworkInfo
    from ..utils.logger import log_debug
else:
    # 如果作為主程式執行，提供假的 log_debug
    def log_debug(msg):
        print(f"[DEBUG] {msg}")


@dataclass
class NetworkMapping:
    """網路映射資訊"""
    standard_name: str  # 標準化名稱 (如 "BSC")
    aliases: List[str]  # 別名列表 (如 ["BSC", "BEP20", "BNB Smart Chain"])
    

@dataclass  
class CoinVariant:
    """幣種變體資訊"""
    exchange: str           # 交易所名稱
    symbol: str            # 幣種符號
    network: str           # 網路名稱
    contract_address: str  # 合約地址
    is_verified: bool = True  # 是否已驗證為同一幣種
    source: str = "smart"    # 來源標記: "traditional" 或 "smart"


@dataclass
class CoinIdentificationResult:
    """幣種識別結果"""
    original_symbol: str                    # 原始輸入的幣種符號
    verified_matches: List[CoinVariant]     # 已驗證的匹配項目
    possible_matches: List[CoinVariant]     # 可能的匹配項目
    debug_info: List[Dict]                  # 除錯資訊 (同名但不同合約的情況)


class NetworkStandardizer:
    """網路名稱標準化器"""
    
    def __init__(self):
        self.network_mappings = self._create_network_mappings()
        
    def _create_network_mappings(self) -> Dict[str, NetworkMapping]:
        """建立網路映射表"""
        mappings = {
            "BSC": NetworkMapping(
                standard_name="BSC",
                aliases=["BSC", "BEP20", "BNB Smart Chain", "BNB Smart Chain (BEP20)", "BEP-20"]
            ),
            "ETH": NetworkMapping(
                standard_name="ETH", 
                aliases=["ETH", "ERC20", "Ethereum", "Ethereum (ERC20)", "ERC-20"]
            ),
            "TRX": NetworkMapping(
                standard_name="TRX",
                aliases=["TRX", "TRC20", "Tron", "Tron (TRC20)", "TRC-20"]
            ),
            "ARBITRUM": NetworkMapping(
                standard_name="ARBITRUM",
                aliases=["ARBITRUM", "ArbitrumOne", "Arbitrum One", "ARBI", "ARB"]
            ),
            "POLYGON": NetworkMapping(
                standard_name="POLYGON",
                aliases=["MATIC", "Polygon", "Polygon PoS", "Polygon POS", "POLYGON"]
            ),
            "OPTIMISM": NetworkMapping(
                standard_name="OPTIMISM", 
                aliases=["OPTIMISM", "Optimism", "OP", "OP Mainnet"]
            ),
            "AVAX": NetworkMapping(
                standard_name="AVAX",
                aliases=["AVAXC", "AVAX C-Chain", "CAVAX", "Avalanche C-Chain", "AVAX-C"]
            ),
            "SOL": NetworkMapping(
                standard_name="SOL",
                aliases=["SOL", "Solana"]
            ),
            "BTC": NetworkMapping(
                standard_name="BTC",
                aliases=["BTC", "Bitcoin"]
            ),
            "XRP": NetworkMapping(
                standard_name="XRP", 
                aliases=["XRP", "XRP Ledger"]
            ),
            "TON": NetworkMapping(
                standard_name="TON",
                aliases=["TON", "The Open Network"]
            ),
            "APTOS": NetworkMapping(
                standard_name="APTOS",
                aliases=["APT", "Aptos"]
            ),
            "BRC20": NetworkMapping(
                standard_name="BRC20",
                aliases=["BRC20", "ORDIBTC", "ORDI-BRC20", "BTC"]
            )
        }
        return mappings
    
    def standardize_network(self, network_name: str) -> str:
        """標準化網路名稱"""
        if not network_name:
            return ""
            
        # 移除括號內容和多餘空格
        cleaned = re.sub(r'\([^)]*\)', '', network_name).strip().upper()
        
        # 查找映射
        for standard_name, mapping in self.network_mappings.items():
            if cleaned in [alias.upper() for alias in mapping.aliases]:
                return standard_name
                
        # 如果沒找到映射，返回清理後的名稱
        return cleaned
    
    def get_network_aliases(self, standard_name: str) -> List[str]:
        """獲取網路的所有別名"""
        mapping = self.network_mappings.get(standard_name.upper())
        return mapping.aliases if mapping else [standard_name]


class CoinIdentifier:
    """跨交易所幣種識別器"""
    
    def __init__(self):
        self.network_standardizer = NetworkStandardizer()
    
    def identify_currency(self, currency: str, searchable_data: Dict[str, List]) -> CoinIdentificationResult:
        """
        統一的幣種識別介面
        
        Args:
            currency: 用戶輸入的幣種符號
            searchable_data: 各交易所的 SearchableCoinInfo 數據
            
        Returns:
            CoinIdentificationResult: 包含傳統查詢和智能識別的完整結果
        """
        log_debug(f"CoinIdentifier 開始識別幣種: {currency}")
        
        # 執行傳統查詢（直接符號匹配和 denomination 處理）
        traditional_results = self._search_from_cached_data(currency, searchable_data)
        log_debug(f"傳統查詢結果: {len(sum(traditional_results.values(), []))} 個網路")
        
        # 執行智能識別（基於合約地址的跨交易所匹配）
        smart_results = self._smart_identification_from_cached_data(currency, searchable_data)
        log_debug(f"智能識別結果: {len(smart_results)} 個額外匹配")
        
        # 合併結果
        all_matches = []
        all_matches.extend(self._convert_traditional_to_variants(traditional_results, currency))
        all_matches.extend(smart_results)
        
        # 去重處理
        verified_matches = self._deduplicate_matches(all_matches)
        
        return CoinIdentificationResult(
            original_symbol=currency,
            verified_matches=verified_matches,
            possible_matches=[],
            debug_info=[]
        )
    
    def _search_from_cached_data(self, currency: str, searchable_data: Dict[str, List]) -> Dict[str, List]:
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
                        from ..exchanges.base import NetworkInfo
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
    
    def _smart_identification_from_cached_data(self, currency: str, searchable_data: Dict[str, List]) -> List[CoinVariant]:
        """從快取數據執行智能識別（基於合約地址的跨交易所匹配），排除傳統查詢已找到的項目"""
        contract_map = {}  # {standardized_contract_key: [(exchange, symbol, original_network)]}
        variants = []
        
        # 首先獲取傳統查詢的結果，用於過濾重複項
        traditional_found = set()  # (exchange, symbol, network)
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                # 檢查是否匹配：直接匹配或去除 denomination 後匹配
                symbol_matches = False
                
                # 直接匹配
                if coin.symbol.upper() == currency.upper():
                    symbol_matches = True
                
                # 檢查 denomination 匹配
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
                        traditional_found.add((exchange_name, coin.symbol, network.network))
        
        log_debug(f"智能識別：傳統查詢已找到 {len(traditional_found)} 個項目")
        
        # 收集所有合約地址映射（使用標準化網路名稱）
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                for network in coin.networks:
                    if network.contract_address:
                        # 使用標準化網路名稱
                        std_network = self.network_standardizer.standardize_network(network.network)
                        contract_key = f"{network.contract_address.lower()}_{std_network}"
                        if contract_key not in contract_map:
                            contract_map[contract_key] = []
                        contract_map[contract_key].append((exchange_name, coin.symbol, network.network))
        
        log_debug(f"智能識別：收集到 {len(contract_map)} 個標準化合約地址映射")
        
        # 找出與輸入幣種相關的合約地址
        input_contracts = set()
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                # 檢查所有可能匹配的符號
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
                            std_network = self.network_standardizer.standardize_network(network.network)
                            contract_key = f"{network.contract_address.lower()}_{std_network}"
                            input_contracts.add(contract_key)
        
        log_debug(f"{currency} 相關的標準化合約地址: {len(input_contracts)} 個")
        
        # 第一階段：找出所有使用相同合約地址的幣種
        related_symbols = set()
        for contract_key in input_contracts:
            if contract_key in contract_map:
                entries = contract_map[contract_key]
                for exchange, symbol, original_network in entries:
                    related_symbols.add(symbol.upper())
        
        log_debug(f"找到 {len(related_symbols)} 個相關幣種符號: {related_symbols}")
        
        # 第二階段：獲取所有相關幣種的所有網路
        all_related_contracts = set()
        for exchange_name, coins in searchable_data.items():
            for coin in coins:
                if coin.symbol.upper() in related_symbols:
                    for network in coin.networks:
                        if network.contract_address:
                            std_network = self.network_standardizer.standardize_network(network.network)
                            contract_key = f"{network.contract_address.lower()}_{std_network}"
                            all_related_contracts.add(contract_key)
        
        log_debug(f"擴展後總共有 {len(all_related_contracts)} 個相關合約地址")
        
        # 第三階段：返回所有相關合約的所有變體（排除傳統查詢已找到的）
        for contract_key in all_related_contracts:
            if contract_key in contract_map:
                entries = contract_map[contract_key]
                for exchange, symbol, original_network in entries:
                    # 檢查是否已被傳統查詢找到
                    if (exchange, symbol, original_network) not in traditional_found:
                        variants.append(CoinVariant(
                            exchange=exchange,
                            symbol=symbol,
                            network=original_network,
                            contract_address=contract_key.split('_')[0],
                            is_verified=True,
                            source="smart"
                        ))
        
        log_debug(f"智能識別最終找到 {len(variants)} 個額外變體")
        return variants
    
    def _convert_traditional_to_variants(self, traditional_results: Dict[str, List], currency: str) -> List[CoinVariant]:
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
    
    def _deduplicate_matches(self, matches: List[CoinVariant]) -> List[CoinVariant]:
        """去重處理"""
        seen = set()
        verified_matches = []
        
        for match in matches:
            # 使用更寬鬆的去重鍵
            if match.contract_address and match.contract_address.strip():
                key = (match.exchange, match.symbol, match.network, match.contract_address.lower())
            else:
                key = (match.exchange, match.symbol, match.network)
            
            if key not in seen:
                seen.add(key)
                verified_matches.append(match)
        
        return verified_matches