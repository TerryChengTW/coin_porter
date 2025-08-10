import asyncio
from typing import Dict, List, Optional
from .base import BaseExchange, NetworkInfo, TransferResult, AccountConfig

try:
    from binance_common.configuration import ConfigurationRestAPI
    from binance_common.constants import WALLET_REST_API_PROD_URL, WALLET_REST_API_TEST_URL
    from binance_sdk_wallet.wallet import Wallet
except ImportError:
    # SDK 未安裝時的處理
    pass


class BinanceExchange(BaseExchange):
    """Binance 交易所實作"""
    
    def __init__(self, account_config: Optional[AccountConfig] = None):
        super().__init__(account_config)
        self._client = None
        
        if account_config:
            self._setup_client()
    
    def _setup_client(self):
        """設定 Binance 客戶端"""
        if not self.account_config:
            return
            
        base_url = WALLET_REST_API_TEST_URL if self.account_config.testnet else WALLET_REST_API_PROD_URL
        
        configuration = ConfigurationRestAPI(
            api_key=self.account_config.api_key,
            api_secret=self.account_config.secret,
            base_path=base_url
        )
        
        self._client = Wallet(config_rest_api=configuration)
    
    async def get_supported_currencies(self) -> List[str]:
        """獲取支援的幣種列表（需要認證）"""
        self._ensure_auth()
        
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
                currencies.append(coin_info.get('coin', ''))
            
            return sorted(list(set(currencies)))  # 去重並排序
            
        except Exception as e:
            raise Exception(f"Binance 查詢支援幣種失敗: {str(e)}")
    
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
            
            # 尋找指定幣種
            for coin_info in data:
                if coin_info.get('coin') == currency.upper():
                    networks = []
                    for network_info in coin_info.get('networkList', []):
                        networks.append(NetworkInfo(
                            network=network_info.get('network', ''),
                            min_withdrawal=float(network_info.get('withdrawMin', 0)),
                            withdrawal_fee=float(network_info.get('withdrawFee', 0)),
                            deposit_enabled=network_info.get('depositEnable', False),
                            withdrawal_enabled=network_info.get('withdrawEnable', False)
                        ))
                    return networks
            
            return []  # 找不到該幣種
            
        except Exception as e:
            raise Exception(f"Binance 查詢幣種網路資訊失敗: {str(e)}")
    
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