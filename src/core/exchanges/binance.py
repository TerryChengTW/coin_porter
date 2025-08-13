import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .base import BaseExchange, NetworkInfo, CoinInfo, TransferResult, AccountConfig, RawCoinData, SearchableCoinInfo, SearchableNetworkInfo

try:
    from binance_common.configuration import ConfigurationRestAPI
    from binance_common.constants import WALLET_REST_API_PROD_URL
    from binance_sdk_wallet.wallet import Wallet
except ImportError:
    # SDK 未安裝時的處理
    ConfigurationRestAPI = None
    WALLET_REST_API_PROD_URL = None
    Wallet = None


class BinanceExchange(BaseExchange):
    """Binance 交易所實作"""
    
    def __init__(self, account_config: Optional[AccountConfig] = None):
        super().__init__(account_config)
        self._client = None
        
        if account_config:
            self._setup_client()
    
    def _setup_client(self):
        """設定 Binance 客戶端"""
        if not self.account_config or not Wallet:
            return
            
        configuration = ConfigurationRestAPI(
            api_key=self.account_config.api_key,
            api_secret=self.account_config.secret,
            base_path=WALLET_REST_API_PROD_URL
        )
        
        self._client = Wallet(config_rest_api=configuration)
    
    async def get_supported_currencies(self) -> List[str]:
        """獲取支援的幣種列表（需要認證）"""
        self._ensure_auth()
        
        if not self._client:
            raise Exception("Binance client not available - SDK may not be installed")
        
        try:
            # 在執行緒池中執行同步呼叫
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.rest_api.all_coins_information()
            )
            
            data = response.data()
            
            # 提取幣種名稱
            currencies = []
            for coin_info in data:
                # Binance SDK 回傳的是物件，不是字典
                coin = getattr(coin_info, 'coin', '')
                if coin:
                    currencies.append(coin)
            
            return sorted(list(set(currencies)))  # 去重並排序
            
        except Exception as e:
            raise Exception(f"Binance query failed: {str(e)}")
    
    async def get_currency_networks(self, currency: str) -> List[NetworkInfo]:
        """獲取指定幣種支援的網路資訊（需要認證）"""
        self._ensure_auth()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.rest_api.all_coins_information()
            )
            
            data = response.data()
            
            # 尋找指定幣種（支持 denomination 匹配）
            for coin_info in data:
                coin_symbol = getattr(coin_info, 'coin', '')
                
                # 直接匹配
                symbol_matches = coin_symbol == currency.upper()
                
                # 檢查 denomination 匹配
                if not symbol_matches:
                    network_list = getattr(coin_info, 'network_list', [])
                    if network_list:
                        first_net = network_list[0]
                        denomination = getattr(first_net, 'denomination', None)
                        if denomination and denomination > 1:
                            # 如果幣種符號以 denomination 數字開頭，去掉前綴比較
                            if coin_symbol.startswith(str(denomination)):
                                base_symbol = coin_symbol[len(str(denomination)):]
                                if base_symbol.upper() == currency.upper():
                                    symbol_matches = True
                
                if symbol_matches:
                    networks = []
                    network_list = getattr(coin_info, 'network_list', [])
                    for network_info in network_list:
                        networks.append(NetworkInfo(
                            network=getattr(network_info, 'network', ''),
                            min_withdrawal=float(getattr(network_info, 'withdraw_min', 0)),
                            withdrawal_fee=float(getattr(network_info, 'withdraw_fee', 0)),
                            deposit_enabled=getattr(network_info, 'deposit_enable', False),
                            withdrawal_enabled=getattr(network_info, 'withdraw_enable', False),
                            contract_address=getattr(network_info, 'contract_address', None),
                            network_full_name=getattr(network_info, 'name', None),
                            browser_url=getattr(network_info, 'contract_address_url', None)
                        ))
                    return networks
            
            return []  # 找不到該幣種
            
        except Exception as e:
            raise Exception(f"Binance 查詢幣種網路資訊失敗: {str(e)}")
    
    async def get_all_coins_info(self) -> Tuple[List[RawCoinData], List[SearchableCoinInfo]]:
        """獲取所有幣種的完整資訊，返回原始數據和搜索用數據"""
        self._ensure_auth()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.rest_api.all_coins_information()
            )
            
            data = response.data()
            raw_data = []
            searchable_data = []
            timestamp = datetime.now().isoformat()
            
            for coin_info in data:
                symbol = getattr(coin_info, 'coin', '')
                if not symbol:
                    continue
                
                # 將 SDK 對象轉換為字典格式以便儲存
                coin_dict = self._convert_coin_object_to_dict(coin_info)
                
                # 創建原始數據
                raw_coin = RawCoinData(
                    exchange="binance",
                    raw_response=coin_dict,
                    timestamp=timestamp
                )
                raw_data.append(raw_coin)
                
                # 創建搜索用數據
                searchable_networks = []
                network_list = getattr(coin_info, 'network_list', [])
                
                # 獲取 denomination（從第一個網路取得）
                denomination = None
                if network_list:
                    first_net = network_list[0]
                    net_denomination = getattr(first_net, 'denomination', None)
                    if net_denomination and net_denomination > 1:
                        denomination = net_denomination
                
                for network_info in network_list:
                    searchable_net = SearchableNetworkInfo(
                        network=getattr(network_info, 'network', ''),
                        deposit_enabled=getattr(network_info, 'deposit_enable', False),
                        withdrawal_enabled=getattr(network_info, 'withdraw_enable', False),
                        withdrawal_fee=float(getattr(network_info, 'withdraw_fee', 0)),
                        min_deposit=None,  # Binance 沒有明確的最小充值額
                        min_withdrawal=float(getattr(network_info, 'withdraw_min', 0)),
                        max_withdrawal=float(getattr(network_info, 'withdraw_max', 0)) if getattr(network_info, 'withdraw_max', None) else None,
                        contract_address=getattr(network_info, 'contract_address', None),
                        browser_url=getattr(network_info, 'contract_address_url', None),
                        busy=getattr(network_info, 'busy', None),
                        estimated_arrival_time=getattr(network_info, 'estimated_arrival_time', None),
                        deposit_desc=getattr(network_info, 'deposit_desc', None),
                        withdraw_desc=getattr(network_info, 'withdraw_desc', None)
                    )
                    searchable_networks.append(searchable_net)
                
                searchable_coin = SearchableCoinInfo(
                    exchange="binance",
                    symbol=symbol,
                    name=getattr(coin_info, 'name', symbol),
                    denomination=denomination,
                    networks=searchable_networks
                )
                searchable_data.append(searchable_coin)
            
            return raw_data, searchable_data
            
        except Exception as e:
            raise Exception(f"Binance 查詢所有幣種資訊失敗: {str(e)}")
    
    def _convert_coin_object_to_dict(self, coin_obj) -> dict:
        """將 Binance SDK 的幣種對象轉換為字典"""
        try:
            # 提取幣種基本信息
            result = {
                'coin': getattr(coin_obj, 'coin', ''),
                'depositAllEnable': getattr(coin_obj, 'deposit_all_enable', False),
                'withdrawAllEnable': getattr(coin_obj, 'withdraw_all_enable', False),
                'name': getattr(coin_obj, 'name', ''),
                'free': getattr(coin_obj, 'free', ''),
                'locked': getattr(coin_obj, 'locked', ''),
                'freeze': getattr(coin_obj, 'freeze', ''),
                'withdrawing': getattr(coin_obj, 'withdrawing', ''),
                'ipoing': getattr(coin_obj, 'ipoing', ''),
                'ipoable': getattr(coin_obj, 'ipoable', ''),
                'storage': getattr(coin_obj, 'storage', ''),
                'isLegalMoney': getattr(coin_obj, 'is_legal_money', False),
                'trading': getattr(coin_obj, 'trading', False),
                'networkList': []
            }
            
            # 轉換網路列表
            network_list = getattr(coin_obj, 'network_list', [])
            for network in network_list:
                network_dict = {
                    'network': getattr(network, 'network', ''),
                    'coin': getattr(network, 'coin', ''),
                    'withdrawIntegerMultiple': getattr(network, 'withdraw_integer_multiple', ''),
                    'isDefault': getattr(network, 'is_default', False),
                    'depositEnable': getattr(network, 'deposit_enable', False),
                    'withdrawEnable': getattr(network, 'withdraw_enable', False),
                    'depositDesc': getattr(network, 'deposit_desc', ''),
                    'withdrawDesc': getattr(network, 'withdraw_desc', ''),
                    'specialTips': getattr(network, 'special_tips', ''),
                    'specialWithdrawTips': getattr(network, 'special_withdraw_tips', ''),
                    'name': getattr(network, 'name', ''),
                    'resetAddressStatus': getattr(network, 'reset_address_status', False),
                    'addressRegex': getattr(network, 'address_regex', ''),
                    'memoRegex': getattr(network, 'memo_regex', ''),
                    'withdrawFee': getattr(network, 'withdraw_fee', ''),
                    'withdrawMin': getattr(network, 'withdraw_min', ''),
                    'withdrawMax': getattr(network, 'withdraw_max', ''),
                    'minConfirm': getattr(network, 'min_confirm', 0),
                    'unLockConfirm': getattr(network, 'un_lock_confirm', 0),
                    'sameAddress': getattr(network, 'same_address', False),
                    'estimatedArrivalTime': getattr(network, 'estimated_arrival_time', 0),
                    'busy': getattr(network, 'busy', False),
                    'contractAddressUrl': getattr(network, 'contract_address_url', ''),
                    'contractAddress': getattr(network, 'contract_address', '')
                }
                result['networkList'].append(network_dict)
            
            return result
            
        except Exception as e:
            # 如果轉換失敗，返回基本信息
            return {
                'coin': getattr(coin_obj, 'coin', ''),
                'error': f"轉換失敗: {str(e)}"
            }
    
    async def get_deposit_address(self, currency: str, network: str) -> str:
        """獲取入金地址"""
        self._ensure_auth()
        # TODO: 實作入金地址查詢
        raise NotImplementedError("get_deposit_address 尚未實作")
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, float]:
        """查詢餘額"""
        self._ensure_auth()
        # TODO: 實作餘額查詢
        raise NotImplementedError("get_balance 尚未實作")
    
    async def withdraw(
        self, 
        currency: str, 
        amount: float, 
        address: str, 
        network: str,
        memo: Optional[str] = None
    ) -> TransferResult:
        """執行出金"""
        self._ensure_auth()
        # TODO: 實作出金功能
        raise NotImplementedError("withdraw 尚未實作")
    
    async def get_transfer_status(self, transfer_id: str) -> TransferResult:
        """查詢轉帳狀態"""
        self._ensure_auth()
        # TODO: 實作轉帳狀態查詢
        raise NotImplementedError("get_transfer_status 尚未實作")
    
    async def get_withdrawal_history(
        self, 
        currency: Optional[str] = None, 
        limit: int = 50
    ) -> List[Dict]:
        """查詢出金歷史"""
        self._ensure_auth()
        # TODO: 實作出金歷史查詢
        raise NotImplementedError("get_withdrawal_history 尚未實作")