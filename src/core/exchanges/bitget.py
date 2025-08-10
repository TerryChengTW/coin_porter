import asyncio
from typing import Dict, List, Optional
from .base import BaseExchange, NetworkInfo, TransferResult, AccountConfig

try:
    from bitget.v2.spot.market_api import MarketApi
    from bitget.bitget_api import BitgetApi
except ImportError:
    # SDK 未安裝時的處理
    pass


class BitgetExchange(BaseExchange):
    """Bitget 交易所實作"""
    
    def __init__(self, account_config: Optional[AccountConfig] = None):
        super().__init__(account_config)
        self._public_client = None  # 公開 API 不需認證
        self._private_client = None  # 私有 API 需認證
        
        # 公開 API 始終可用
        self._setup_public_client()
        
        if account_config:
            self._setup_private_client()
    
    def _setup_public_client(self):
        """設定 Bitget 公開客戶端（不需認證）"""
        try:
            # 公開 API 不需要認證資訊
            self._public_client = MarketApi("", "", "")
        except:
            pass
    
    def _setup_private_client(self):
        """設定 Bitget 私有客戶端"""
        if not self.account_config:
            return
            
        self._private_client = BitgetApi(
            api_key=self.account_config.api_key,
            api_secret_key=self.account_config.secret,
            passphrase=self.account_config.passphrase,
            use_server_time=False,
            first=False
        )
    
    async def get_supported_currencies(self) -> List[str]:
        """獲取支援的幣種列表（公開端點，不需認證）"""
        if not self._public_client:
            raise Exception("Bitget 公開客戶端未初始化")
        
        try:
            # 使用公開端點查詢所有幣種
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._public_client.coins({})
            )
            
            if response.get('code') != '00000':
                raise Exception(f"Bitget API 錯誤: {response.get('msg', 'Unknown error')}")
            
            # 提取幣種名稱
            currencies = []
            for coin_info in response.get('data', []):
                coin = coin_info.get('coinName', '')
                if coin:
                    currencies.append(coin)
            
            return sorted(list(set(currencies)))  # 去重並排序
            
        except Exception as e:
            raise Exception(f"Bitget 查詢支援幣種失敗: {str(e)}")
    
    async def get_currency_networks(self, currency: str) -> List[NetworkInfo]:
        """獲取指定幣種支援的網路資訊（公開端點）"""
        if not self._public_client:
            raise Exception("Bitget 公開客戶端未初始化")
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._public_client.coins({"coin": currency.upper()})
            )
            
            if response.get('code') != '00000':
                raise Exception(f"Bitget API 錯誤: {response.get('msg', 'Unknown error')}")
            
            networks = []
            for coin_info in response.get('data', []):
                if coin_info.get('coinName') == currency.upper():
                    for chain_info in coin_info.get('chains', []):
                        networks.append(NetworkInfo(
                            network=chain_info.get('chain', ''),
                            min_withdrawal=float(chain_info.get('minWithdrawAmount', 0)),
                            withdrawal_fee=float(chain_info.get('withdrawFee', 0)),
                            deposit_enabled=chain_info.get('rechargeable', False),
                            withdrawal_enabled=chain_info.get('withdrawable', False)
                        ))
                    break
            
            return networks
            
        except Exception as e:
            raise Exception(f"Bitget 查詢幣種網路資訊失敗: {str(e)}")
    
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