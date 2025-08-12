import asyncio
from typing import Dict, List, Optional
from .base import BaseExchange, NetworkInfo, CoinInfo, TransferResult, AccountConfig

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
            
            # 尋找指定幣種
            for coin_info in data:
                if getattr(coin_info, 'coin', '') == currency.upper():
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
    
    async def get_all_coins_info(self) -> List[CoinInfo]:
        """獲取所有幣種的完整資訊"""
        self._ensure_auth()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.rest_api.all_coins_information()
            )
            
            data = response.data()
            coins = []
            
            for coin_info in data:
                symbol = getattr(coin_info, 'coin', '')
                if not symbol:
                    continue
                    
                # 解析網路資訊
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
                
                # 創建 CoinInfo
                coin = CoinInfo(
                    symbol=symbol,
                    full_name=getattr(coin_info, 'name', symbol),
                    trading_enabled=getattr(coin_info, 'trading', False),
                    deposit_all_enabled=getattr(coin_info, 'deposit_all_enable', False),
                    withdrawal_all_enabled=getattr(coin_info, 'withdraw_all_enable', False),
                    networks=networks
                )
                coins.append(coin)
            
            return coins
            
        except Exception as e:
            raise Exception(f"Binance 查詢所有幣種資訊失敗: {str(e)}")
    
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