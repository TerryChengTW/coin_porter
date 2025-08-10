import asyncio
from typing import Dict, List, Optional
from .base import BaseExchange, NetworkInfo, TransferResult, AccountConfig

try:
    import sys
    import os
    # 添加 Bitget SDK 路徑
    sdk_path = os.path.join(os.path.dirname(__file__), '..', '..', 'third-party', 'bitget-sdk')
    if sdk_path not in sys.path:
        sys.path.append(sdk_path)
    
    from v2.spot.market_api import MarketApi
    from bitget_api import BitgetApi
except ImportError:
    # SDK 未安裝時的處理
    MarketApi = None
    BitgetApi = None


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
        """設定 Bitget 公開客戶端（實際上 MarketApi 仍需認證）"""
        # Bitget 的 MarketApi 實際上需要認證，沒有純公開版本
        self._public_client = None
    
    def _setup_private_client(self):
        """設定 Bitget 私有客戶端"""
        if not self.account_config or not MarketApi:
            return
            
        # 使用 MarketApi 來查詢市場資料
        self._private_client = MarketApi(
            api_key=self.account_config.api_key,
            api_secret_key=self.account_config.secret,
            passphrase=self.account_config.passphrase,
            use_server_time=False,
            first=False
        )
    
    async def get_supported_currencies(self) -> List[str]:
        """獲取支援的幣種列表（需要認證）"""
        self._ensure_auth()
        
        if not self._private_client:
            raise Exception("Bitget client not available - SDK may not be installed")
        
        try:
            # 使用認證端點查詢所有幣種
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._private_client.public_coins({})
            )
            
            if response.get('code') != '00000':
                raise Exception(f"Bitget API 錯誤: {response.get('msg', 'Unknown error')}")
            
            # 提取幣種名稱
            currencies = []
            for coin_info in response.get('data', []):
                coin = coin_info.get('coin', '')  # Bitget 使用 'coin' 而不是 'coinName'
                if coin:
                    currencies.append(coin)
            
            return sorted(list(set(currencies)))  # 去重並排序
            
        except Exception as e:
            raise Exception(f"Bitget query failed: {str(e)}")
    
    async def get_currency_networks(self, currency: str) -> List[NetworkInfo]:
        """獲取指定幣種支援的網路資訊（需要認證）"""
        self._ensure_auth()
        
        if not self._private_client:
            raise Exception("Bitget client not available")
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._private_client.public_coins({"coin": currency.upper()})
            )
            
            if response.get('code') != '00000':
                raise Exception(f"Bitget API 錯誤: {response.get('msg', 'Unknown error')}")
            
            networks = []
            for coin_info in response.get('data', []):
                if coin_info.get('coin') == currency.upper():  # 使用 'coin' 而不是 'coinName'
                    for chain_info in coin_info.get('chains', []):
                        networks.append(NetworkInfo(
                            network=chain_info.get('chain', ''),
                            min_withdrawal=float(chain_info.get('minWithdrawAmount', 0)),
                            withdrawal_fee=float(chain_info.get('withdrawFee', 0)),
                            deposit_enabled=chain_info.get('rechargeable') == 'true',  # 字串比較
                            withdrawal_enabled=chain_info.get('withdrawable') == 'true'  # 字串比較
                        ))
                    break
            
            return networks
            
        except Exception as e:
            raise Exception(f"Bitget network query failed: {str(e)}")
    
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