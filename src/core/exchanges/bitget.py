import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .base import BaseExchange, NetworkInfo, CoinInfo, TransferResult, AccountConfig, RawCoinData, SearchableCoinInfo, SearchableNetworkInfo

try:
    import sys
    import os
    # 添加 Bitget SDK 路徑
    sdk_path = os.path.join(os.path.dirname(__file__), '..', '..', 'third-party')
    if sdk_path not in sys.path:
        sys.path.insert(0, sdk_path)  # 插入到最前面，優先使用本地 SDK
    
    from bitget.v2.spot.market_api import MarketApi
    from bitget.bitget_api import BitgetApi
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
    
    async def get_all_coins_info(self) -> Tuple[List[RawCoinData], List[SearchableCoinInfo]]:
        """獲取所有幣種的完整資訊，返回原始數據和搜索用數據"""
        self._ensure_auth()
        
        if not self._private_client:
            raise Exception("Bitget client not available")
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._private_client.public_coins({})  # 空參數獲取所有幣種
            )
            
            if response.get('code') != '00000':
                raise Exception(f"Bitget API 錯誤: {response.get('msg', 'Unknown error')}")
            
            raw_data = []
            searchable_data = []
            timestamp = datetime.now().isoformat()
            
            total_coins = len(response.get('data', []))
            
            for coin_info in response.get('data', []):
                symbol = coin_info.get('coin', '')
                if not symbol:
                    continue
                
                # 創建原始數據
                raw_coin = RawCoinData(
                    exchange="bitget",
                    raw_response=coin_info,  # Bitget 回應已經是字典格式
                    timestamp=timestamp
                )
                raw_data.append(raw_coin)
                
                # 創建搜索用數據
                searchable_networks = []
                for chain_info in coin_info.get('chains', []):
                    # 安全轉換數值
                    min_withdraw_str = chain_info.get('minWithdrawAmount', '0')
                    withdraw_fee_str = chain_info.get('withdrawFee', '0')
                    min_deposit_str = chain_info.get('minDepositAmount', '0')
                    extra_withdraw_fee_str = chain_info.get('extraWithdrawFee', '0')
                    
                    searchable_net = SearchableNetworkInfo(
                        network=chain_info.get('chain', ''),
                        deposit_enabled=chain_info.get('rechargeable') == 'true',
                        withdrawal_enabled=chain_info.get('withdrawable') == 'true',
                        withdrawal_fee=float(withdraw_fee_str) if withdraw_fee_str else 0.0,
                        extra_withdraw_fee=float(extra_withdraw_fee_str) if extra_withdraw_fee_str and extra_withdraw_fee_str != '0' else None,
                        min_deposit=float(min_deposit_str) if min_deposit_str and min_deposit_str != '0' else None,
                        min_withdrawal=float(min_withdraw_str) if min_withdraw_str else 0.0,
                        contract_address=chain_info.get('contractAddress') if chain_info.get('contractAddress') else None,
                        browser_url=chain_info.get('browserUrl') if chain_info.get('browserUrl') else None,
                        congestion=chain_info.get('congestion') if chain_info.get('congestion') else None
                    )
                    searchable_networks.append(searchable_net)
                
                searchable_coin = SearchableCoinInfo(
                    exchange="bitget",
                    symbol=symbol,
                    name=symbol,  # Bitget 沒有提供完整名稱，使用符號
                    networks=searchable_networks
                )
                searchable_data.append(searchable_coin)
            
            return raw_data, searchable_data
            
        except Exception as e:
            raise Exception(f"Bitget 查詢所有幣種資訊失敗: {str(e)}")
    
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