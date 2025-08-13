import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .base import BaseExchange, NetworkInfo, CoinInfo, TransferResult, AccountConfig, RawCoinData, SearchableCoinInfo, SearchableNetworkInfo

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
                        # 安全轉換數值，處理空字串
                        withdraw_min_str = chain_info.get('withdrawMin', '0')
                        withdraw_fee_str = chain_info.get('withdrawFee', '0')
                        
                        networks.append(NetworkInfo(
                            network=chain_info.get('chain', ''),
                            min_withdrawal=float(withdraw_min_str) if withdraw_min_str and withdraw_min_str.strip() else 0.0,
                            withdrawal_fee=float(withdraw_fee_str) if withdraw_fee_str and withdraw_fee_str.strip() else 0.0,
                            deposit_enabled=chain_info.get('chainDeposit') == '1',
                            withdrawal_enabled=chain_info.get('chainWithdraw') == '1'
                        ))
                    break
            
            return networks
            
        except Exception as e:
            raise Exception(f"Bybit 查詢幣種網路資訊失敗: {str(e)}")
    
    async def get_all_coins_info(self) -> Tuple[List[RawCoinData], List[SearchableCoinInfo]]:
        """獲取所有幣種的完整資訊，返回原始數據和搜索用數據"""
        self._ensure_auth()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.get_coin_info()  # 無參數版本，獲取所有幣種
            )
            
            if response.get('retCode') != 0:
                raise Exception(f"Bybit API 錯誤: {response.get('retMsg', 'Unknown error')}")
            
            raw_data = []
            searchable_data = []
            timestamp = datetime.now().isoformat()
            
            for row in response.get('result', {}).get('rows', []):
                symbol = row.get('coin', '')
                if not symbol:
                    continue
                
                # 創建原始數據
                raw_coin = RawCoinData(
                    exchange="bybit",
                    raw_response=row,  # Bybit 回應已經是字典格式
                    timestamp=timestamp
                )
                raw_data.append(raw_coin)
                
                # 創建搜索用數據
                searchable_networks = []
                for chain_info in row.get('chains', []):
                    # 安全轉換數值，處理空字串
                    withdraw_min_str = chain_info.get('withdrawMin', '')
                    withdraw_fee_str = chain_info.get('withdrawFee', '')
                    deposit_min_str = chain_info.get('depositMin', '')
                    withdraw_percentage_fee_str = chain_info.get('withdrawPercentageFee', '')
                    
                    # 如果 withdrawFee 為空，表示該幣不支持提現
                    withdrawal_fee_available = bool(withdraw_fee_str and withdraw_fee_str.strip())
                    
                    searchable_net = SearchableNetworkInfo(
                        network=chain_info.get('chain', ''),
                        chain_type=chain_info.get('chainType', None),  # Bybit 特有欄位
                        deposit_enabled=chain_info.get('chainDeposit') == '1',
                        withdrawal_enabled=withdrawal_fee_available and chain_info.get('chainWithdraw') == '1',
                        withdrawal_fee=float(withdraw_fee_str) if withdrawal_fee_available else 0.0,
                        withdraw_percentage_fee=float(withdraw_percentage_fee_str) if withdraw_percentage_fee_str and withdraw_percentage_fee_str.strip() else None,
                        min_deposit=float(deposit_min_str) if deposit_min_str and deposit_min_str.strip() else None,
                        min_withdrawal=float(withdraw_min_str) if withdraw_min_str and withdraw_min_str.strip() else 0.0,
                        contract_address=chain_info.get('contractAddress') if chain_info.get('contractAddress') else None
                    )
                    searchable_networks.append(searchable_net)
                
                searchable_coin = SearchableCoinInfo(
                    exchange="bybit",
                    symbol=symbol,
                    name=row.get('name', symbol),
                    networks=searchable_networks
                )
                searchable_data.append(searchable_coin)
            
            return raw_data, searchable_data
            
        except Exception as e:
            raise Exception(f"Bybit 查詢所有幣種資訊失敗: {str(e)}")
    
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