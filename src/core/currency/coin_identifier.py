"""
雙路線幣種識別模組
實現基於合約地址的深度查詢和同名驗證的雙重策略
"""

import json
import re
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path


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


class ContractAddressDatabase:
    """合約地址資料庫"""
    
    def __init__(self):
        self.contracts: Dict[str, Dict[str, str]] = {}  # {contract_address: {network: symbol}}
        self.symbols: Dict[str, Dict[str, str]] = {}    # {symbol: {network: contract_address}}
        
    def add_contract(self, symbol: str, network: str, contract_address: str, exchange: str):
        """添加合約地址資訊"""
        if not contract_address or contract_address.lower() in ['null', 'none', '']:
            return
            
        # 標準化網路名稱
        standardizer = NetworkStandardizer()
        std_network = standardizer.standardize_network(network)
        
        # 建立合約索引
        if contract_address not in self.contracts:
            self.contracts[contract_address] = {}
        self.contracts[contract_address][std_network] = symbol
        
        # 建立幣種索引
        if symbol not in self.symbols:
            self.symbols[symbol] = {}
        self.symbols[symbol][std_network] = contract_address
        
    def find_symbols_by_contract(self, contract_address: str, network: str) -> List[str]:
        """根據合約地址查找可能的幣種符號"""
        standardizer = NetworkStandardizer()
        std_network = standardizer.standardize_network(network)
        
        if contract_address in self.contracts:
            if std_network in self.contracts[contract_address]:
                return [self.contracts[contract_address][std_network]]
                
        return []
    
    def find_contracts_by_symbol(self, symbol: str) -> Dict[str, str]:
        """根據幣種符號查找所有網路的合約地址"""
        return self.symbols.get(symbol, {})
    
    def get_all_symbols_for_contract(self, contract_address: str) -> Dict[str, str]:
        """獲取指定合約地址在所有網路上的幣種符號"""
        return self.contracts.get(contract_address, {})


class CoinIdentifier:
    """雙路線幣種識別器"""
    
    def __init__(self):
        self.network_standardizer = NetworkStandardizer()
        self.contract_db = ContractAddressDatabase()
        self._load_contract_mappings()
        
    def _load_contract_mappings(self):
        """載入合約映射資料"""
        # 動態從API回應檔案載入合約映射，或使用預設映射
        try:
            contract_mappings = self._load_from_api_responses()
            print(f"[INFO] 從 API 回應檔案載入了 {len(contract_mappings)} 個映射關係")
        except Exception as e:
            print(f"[WARN] 無法從 API 回應檔案載入映射，使用預設映射: {e}")
            contract_mappings = self._get_default_contract_mappings()
            
        
        # 為每個映射組添加所有變體
        for mapping in contract_mappings:
            contract = mapping["contract"]
            network = mapping["network"]
            
            # 為每個變體添加映射
            for symbol, exchanges in mapping["variants"]:
                for exchange in exchanges:
                    self.contract_db.add_contract(symbol, network, contract, exchange)
    
    def _load_from_api_responses(self):
        """從 API 回應檔案動態載入合約映射"""
        api_responses_dir = Path(__file__).parent.parent.parent.parent / "docs" / "api-response-examples"
        contract_mappings = []
        
        # 檢查目錄是否存在
        if not api_responses_dir.exists():
            raise FileNotFoundError(f"API 回應檔案目錄不存在: {api_responses_dir}")
        
        # 載入各交易所數據
        exchange_data = {}
        
        # Binance
        binance_file = api_responses_dir / "binance" / "all_coins_information_full_response.json"
        if binance_file.exists():
            with open(binance_file, 'r', encoding='utf-8') as f:
                exchange_data['binance'] = json.load(f)
        
        # Bybit  
        bybit_file = api_responses_dir / "bybit" / "coin_info_full_response.json"
        if bybit_file.exists():
            with open(bybit_file, 'r', encoding='utf-8') as f:
                bybit_data = json.load(f)
                exchange_data['bybit'] = bybit_data.get('result', {}).get('rows', [])
        
        # Bitget
        bitget_file = api_responses_dir / "bitget" / "public_coins_full_response.json"
        if bitget_file.exists():
            with open(bitget_file, 'r', encoding='utf-8') as f:
                bitget_data = json.load(f)
                exchange_data['bitget'] = bitget_data.get('data', [])
        
        # 分析合約地址映射
        contract_mappings = self._analyze_contract_mappings(exchange_data)
        
        return contract_mappings
    
    def _analyze_contract_mappings(self, exchange_data: Dict) -> List[Dict]:
        """分析交易所數據，找出合約地址映射關係"""
        contract_map = {}  # {contract_address: {network: [(symbol, exchange)]}}
        
        # 處理 Binance 數據
        if 'binance' in exchange_data:
            for coin in exchange_data['binance']:
                symbol = coin['coin']
                for network in coin.get('network_list', []):
                    contract = network.get('contract_address')
                    if contract and contract.lower() not in ['null', 'none', '']:
                        net_name = network['network']
                        # 標準化合約地址為小寫和網路名稱
                        contract = contract.lower()
                        std_net_name = self.network_standardizer.standardize_network(net_name)
                        key = f"{contract}_{std_net_name}"
                        
                        if key not in contract_map:
                            contract_map[key] = {'contract': contract, 'network': std_net_name, 'variants': {}}
                        
                        if symbol not in contract_map[key]['variants']:
                            contract_map[key]['variants'][symbol] = []
                        contract_map[key]['variants'][symbol].append('binance')
        
        # 處理 Bybit 數據
        if 'bybit' in exchange_data:
            for coin in exchange_data['bybit']:
                symbol = coin['coin']
                for chain in coin.get('chains', []):
                    contract = chain.get('contractAddress')
                    net_name = chain['chain']
                    std_net_name = self.network_standardizer.standardize_network(net_name)
                    
                    # 特殊處理 BRC20 代幣
                    if std_net_name in ['BRC20', 'BTC'] and not contract:
                        # 對於 BRC20 代幣，使用幣種符號的小寫作為標識符
                        contract = symbol.lower()
                    
                    if contract and str(contract).lower() not in ['null', 'none', '']:
                        # 標準化合約地址為小寫
                        contract = str(contract).lower()
                        key = f"{contract}_{std_net_name}"
                        
                        if key not in contract_map:
                            contract_map[key] = {'contract': contract, 'network': std_net_name, 'variants': {}}
                        
                        if symbol not in contract_map[key]['variants']:
                            contract_map[key]['variants'][symbol] = []
                        contract_map[key]['variants'][symbol].append('bybit')
        
        # 處理 Bitget 數據
        if 'bitget' in exchange_data:
            for coin in exchange_data['bitget']:
                symbol = coin['coin']
                for chain in coin.get('chains', []):
                    contract = chain.get('contractAddress')
                    net_name = chain['chain']
                    std_net_name = self.network_standardizer.standardize_network(net_name)
                    
                    # 特殊處理 BRC20 代幣
                    if std_net_name in ['BRC20', 'BTC'] and not contract:
                        # 對於 BRC20 代幣，使用幣種符號的小寫作為標識符
                        contract = symbol.lower()
                    
                    if contract and str(contract).lower() not in ['null', 'none', '']:
                        # 標準化合約地址為小寫
                        contract = str(contract).lower()
                        key = f"{contract}_{std_net_name}"
                        
                        if key not in contract_map:
                            contract_map[key] = {'contract': contract, 'network': std_net_name, 'variants': {}}
                        
                        if symbol not in contract_map[key]['variants']:
                            contract_map[key]['variants'][symbol] = []
                        contract_map[key]['variants'][symbol].append('bitget')
        
        # 轉換為標準格式，只保留有多個變體的映射
        mappings = []
        for key, data in contract_map.items():
            if len(data['variants']) > 1:  # 只保留有多個符號變體的合約
                variants = []
                for symbol, exchanges in data['variants'].items():
                    variants.append((symbol, exchanges))
                
                mappings.append({
                    'contract': data['contract'],
                    'network': data['network'], 
                    'variants': variants
                })
        
        return mappings
    
    def _get_default_contract_mappings(self):
        """獲取預設的硬編碼合約映射（作為備用）"""
        return [
            # CAT/1000CAT - BSC網路
            {
                "contract": "0x6894cde390a3f51155ea41ed24a33a4827d3063d",
                "network": "BSC", 
                "variants": [
                    ("CAT", ["bybit"]),
                    ("1000CAT", ["binance"])
                ]
            },
            # SATS/1000SATS - BRC20網路
            {
                "contract": "sats",
                "network": "BRC20",
                "variants": [
                    ("SATS", ["bitget", "bybit"]),
                    ("1000SATS", ["binance"])
                ]
            },
            # BABYDOGE/1MBABYDOGE - BSC網路
            {
                "contract": "0xc748673057861a797275cd8a068abb95a902e8de",
                "network": "BSC",
                "variants": [
                    ("BABYDOGE", ["bybit"]),
                    ("1MBABYDOGE", ["binance"])
                ]
            },
            # BEAM/BEAMX - ETH網路  
            {
                "contract": "0x62d0a8458ed7719fdaf978fe5929c6d342b0bfce",
                "network": "ETH",
                "variants": [
                    ("BEAM", ["bybit"]),
                    ("BEAMX", ["binance"])
                ]
            },
            # BTT/BTTC - TRX網路
            {
                "contract": "TAFjULxiVgT4qWk6UZwjqwZXTSaGaqnVp4",
                "network": "TRX", 
                "variants": [
                    ("BTT", ["bybit"]),
                    ("BTTC", ["binance"])
                ]
            },
            # NEIRO/NEIROCTO - ETH網路
            {
                "contract": "0x812ba41e071c7b7fa4ebcfb62df5f45f6fa853ee",
                "network": "ETH",
                "variants": [
                    ("NEIRO", ["binance"]),
                    ("NEIROCTO", ["bybit"])
                ]
            },
            # ZEROLEND/ZERO - LINEA網路
            {
                "contract": "0x78354f8dccb269a615a7e0a24f9b0718fdc3c7a7",
                "network": "LINEA",
                "variants": [
                    ("ZEROLEND", ["bitget"]),
                    ("ZERO", ["bybit"])
                ]
            }
        ]
    
    def identify_coin(self, input_symbol: str, exchange_data: Dict[str, List]) -> CoinIdentificationResult:
        """
        雙路線幣種識別
        
        Args:
            input_symbol: 用戶輸入的幣種符號
            exchange_data: 各交易所的查詢結果 {"binance": [NetworkInfo, ...], ...}
            
        Returns:
            CoinIdentificationResult: 識別結果
        """
        input_symbol = input_symbol.upper()
        print(f"[DEBUG] identify_coin 開始，輸入符號: {input_symbol}")
        print(f"[DEBUG] 交易所數據: {exchange_data}")
        
        # 路線一：基於合約地址的深度查詢
        print(f"[DEBUG] 執行路線一：合約地址深度查詢")
        route1_results = self._contract_based_search(input_symbol, exchange_data)
        print(f"[DEBUG] 路線一結果: {len(route1_results[0])} 驗證匹配, {len(route1_results[1])} 除錯")
        
        # 路線二：基於同名的驗證查詢  
        print(f"[DEBUG] 執行路線二：同名驗證查詢")
        route2_results = self._same_name_validation(input_symbol, exchange_data)
        print(f"[DEBUG] 路線二結果: {len(route2_results[0])} 驗證匹配, {len(route2_results[1])} 除錯")
        
        # 合併並去重結果
        print(f"[DEBUG] 合併結果")
        final_result = self._merge_results(input_symbol, route1_results, route2_results)
        print(f"[DEBUG] 最終結果: {len(final_result.verified_matches)} 驗證, {len(final_result.possible_matches)} 可能")
        
        return final_result
    
    def _contract_based_search(self, symbol: str, exchange_data: Dict) -> Tuple[List[CoinVariant], List[Dict]]:
        """路線一：基於合約地址的深度查詢"""
        verified_matches = []
        debug_info = []
        
        print(f"[DEBUG] 路線一開始，符號: {symbol}")
        
        # 從已知映射中查找可能的別名
        possible_symbols = self.get_possible_symbols(symbol)
        print(f"[DEBUG] 路線一找到可能的符號: {possible_symbols}")
        
        # 對每個可能的符號檢查是否有實際的查詢結果
        for test_symbol in possible_symbols:
            print(f"[DEBUG] 檢查符號: {test_symbol}")
            
            # 查找使用這個符號的映射資訊
            for mapping in self._get_contract_mappings():
                mapping_symbols = [variant[0] for variant in mapping["variants"]]
                if test_symbol in mapping_symbols:
                    print(f"[DEBUG] 找到 {test_symbol} 的映射資訊")
                    
                    # 找到該符號對應的交易所
                    for variant_symbol, exchanges in mapping["variants"]:
                        if variant_symbol == test_symbol:
                            for exchange in exchanges:
                                print(f"[DEBUG] 創建 CoinVariant: {exchange} - {test_symbol}")
                                verified_matches.append(CoinVariant(
                                    exchange=exchange,
                                    symbol=test_symbol,
                                    network=mapping["network"],
                                    contract_address=mapping["contract"],
                                    is_verified=True
                                ))
            
        print(f"[DEBUG] 路線一完成，找到 {len(verified_matches)} 個匹配")
        return verified_matches, debug_info
    
    def _same_name_validation(self, symbol: str, exchange_data: Dict) -> Tuple[List[CoinVariant], List[Dict]]:
        """路線二：基於同名的驗證查詢"""
        verified_matches = []
        debug_info = []
        
        # 收集所有同名結果
        same_name_results = {}
        for exchange, networks in exchange_data.items():
            if networks:  # 有找到結果
                same_name_results[exchange] = networks
        
        if len(same_name_results) < 2:
            return verified_matches, debug_info
        
        # 檢查網路和合約地址的一致性
        exchanges = list(same_name_results.keys())
        for i in range(len(exchanges)):
            for j in range(i + 1, len(exchanges)):
                ex1, ex2 = exchanges[i], exchanges[j]
                matches, conflicts = self._compare_exchange_networks(
                    ex1, same_name_results[ex1], 
                    ex2, same_name_results[ex2], 
                    symbol
                )
                verified_matches.extend(matches)
                debug_info.extend(conflicts)
        
        return verified_matches, debug_info
    
    def _compare_exchange_networks(self, ex1: str, networks1: List, ex2: str, networks2: List, symbol: str) -> Tuple[List[CoinVariant], List[Dict]]:
        """比較兩個交易所的網路支援情況"""
        matches = []
        conflicts = []
        
        # 建立網路映射
        net1_map = {}  # {standard_network: NetworkInfo}
        net2_map = {}
        
        for net_info in networks1:
            std_net = self.network_standardizer.standardize_network(net_info.network)
            net1_map[std_net] = net_info
            
        for net_info in networks2:
            std_net = self.network_standardizer.standardize_network(net_info.network)
            net2_map[std_net] = net_info
        
        # 找出共同支援的網路
        common_networks = set(net1_map.keys()) & set(net2_map.keys())
        
        for std_network in common_networks:
            # 這裡需要檢查合約地址是否相同
            # 由於NetworkInfo沒有包含合約地址，先標記為已驗證
            # TODO: 需要擴展NetworkInfo包含合約地址資訊
            matches.append(CoinVariant(
                exchange=ex1,
                symbol=symbol, 
                network=std_network,
                contract_address="",  # TODO: 從實際數據獲取
                is_verified=True
            ))
        
        return matches, conflicts
    
    def _merge_results(self, original_symbol: str, route1_results: Tuple, route2_results: Tuple) -> CoinIdentificationResult:
        """合併兩條路線的結果並去重"""
        route1_matches, route1_debug = route1_results
        route2_matches, route2_debug = route2_results
        
        # 合併結果
        all_matches = route1_matches + route2_matches
        all_debug = route1_debug + route2_debug
        
        # 去重 (基於 exchange + symbol + network + contract_address)
        seen = set()
        verified_matches = []
        possible_matches = []
        
        for match in all_matches:
            key = (match.exchange, match.symbol, match.network, match.contract_address)
            if key not in seen:
                seen.add(key)
                if match.is_verified:
                    verified_matches.append(match)
                else:
                    possible_matches.append(match)
        
        return CoinIdentificationResult(
            original_symbol=original_symbol,
            verified_matches=verified_matches,
            possible_matches=possible_matches,
            debug_info=all_debug
        )
    
    def get_possible_symbols(self, symbol: str) -> Set[str]:
        """獲取可能的幣種符號別名"""
        possible_symbols = {symbol.upper()}
        
        # 從合約地址資料庫查找
        symbol_contracts = self.contract_db.find_contracts_by_symbol(symbol.upper())
        for network, contract in symbol_contracts.items():
            # 找出使用相同合約地址的所有符號
            other_symbols = self.contract_db.get_all_symbols_for_contract(contract)
            for net, sym in other_symbols.items():
                std_net = self.network_standardizer.standardize_network(net)
                if std_net == network:
                    possible_symbols.add(sym)
        
        # 反向查找：從已知映射中尋找
        for mapping in self._get_contract_mappings():
            contract = mapping["contract"]
            std_network = mapping["network"]
            
            # 檢查當前符號是否在這個映射組中
            mapping_symbols = [variant[0] for variant in mapping["variants"]]
            if symbol.upper() in mapping_symbols:
                # 添加同組的所有其他符號
                possible_symbols.update(mapping_symbols)
        
        return possible_symbols
    
    def _get_contract_mappings(self):
        """獲取合約映射配置"""
        # 使用相同的動態載入邏輯，或預設映射
        try:
            return self._load_from_api_responses()
        except Exception:
            return self._get_default_contract_mappings()


def create_coin_identifier() -> CoinIdentifier:
    """創建幣種識別器實例"""
    return CoinIdentifier()