import asyncio
from typing import Dict, List, Optional
from .base import BaseExchange, NetworkInfo, TransferResult, AccountConfig

try:
    from pybit.unified_trading import HTTP
except ImportError:
    # SDK 未安裝時的處理
    pass


class BybitExchange(BaseExchange):
    """Bybit 交易所實作"""
    
    def __init__(self, account_config: Optional[AccountConfig] = None):
        super().__init__(account_config)
        self._client = None
        
        if account_config:
            self._setup_client()
    
    def _setup_client(self):
        """設定 Bybit 客戶端"""
        if not self.account_config:
            return
            
        self._client = HTTP(
            testnet=self.account_config.testnet,
            api_key=self.account_config.api_key,
            api_secret=self.account_config.secret
        )
    
    async def get_supported_currencies(self) -> List[str]:
        """獲取支援的幣種列表（需要認證）"""
        self._ensure_auth()
        
        try:
            # 使用 get_coin_info 查詢所有幣種（傳入空參數）
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.get_coin_info()
            )
            
            if response.get('retCode') != 0:
                raise Exception(f"Bybit API 錯誤: {response.get('retMsg', 'Unknown error')}")
            
            # 提取幣種名稱
            currencies = []
            for row in response.get('result', {}).get('rows', []):
                coin = row.get('coin', '')
                if coin:
                    currencies.append(coin)
            
            return sorted(list(set(currencies)))  # 去重並排序
            
        except Exception as e:
            raise Exception(f"Bybit 查詢支援幣種失敗: {str(e)}")
    
    async def get_currency_networks(self, currency: str) -> List[NetworkInfo]:
        """獲取指定幣種支援的網路資訊（需要認證）"""
        self._ensure_auth()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.get_coin_info(coin=currency.upper())
            )
            
            if response.get('retCode') != 0:
                raise Exception(f"Bybit API 錯誤: {response.get('retMsg', 'Unknown error')}")
            
            networks = []
            for row in response.get('result', {}).get('rows', []):
                if row.get('coin') == currency.upper():
                    for chain_info in row.get('chains', []):
                        networks.append(NetworkInfo(
                            network=chain_info.get('chain', ''),
                            min_withdrawal=float(chain_info.get('withdrawMin', 0)),
                            withdrawal_fee=float(chain_info.get('withdrawFee', 0)),
                            deposit_enabled=chain_info.get('chainDeposit') == '1',
                            withdrawal_enabled=chain_info.get('chainWithdraw') == '1'
                        ))
                    break
            
            return networks
            
        except Exception as e:
            raise Exception(f"Bybit 查詢幣種網路資訊失敗: {str(e)}")
    
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