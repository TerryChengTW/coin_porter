from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class NetworkInfo:
    """網路資訊"""
    network: str
    min_withdrawal: float
    withdrawal_fee: float
    deposit_enabled: bool
    withdrawal_enabled: bool
    contract_address: Optional[str] = None
    network_full_name: Optional[str] = None  # 完整網路名稱
    browser_url: Optional[str] = None        # 區塊鏈瀏覽器URL


@dataclass
class CoinInfo:
    """幣種完整資訊"""
    symbol: str                        # 幣種符號
    full_name: str                     # 完整名稱
    trading_enabled: bool              # 是否支援交易
    deposit_all_enabled: bool          # 是否支援所有網路入金
    withdrawal_all_enabled: bool       # 是否支援所有網路出金
    networks: List[NetworkInfo]        # 支援的網路列表


@dataclass
class RawCoinData:
    """原始完整資料 - 直接儲存API回應"""
    exchange: str                      # 交易所名稱
    raw_response: Dict                 # 完整的原始API回應
    timestamp: str                     # 查詢時間


@dataclass
class SearchableNetworkInfo:
    """智能搜索用的網路資訊 - 只包含重要欄位"""
    # 基本識別類別
    network: str                              # 網路名稱
    chain_type: Optional[str] = None          # 詳細鏈名稱 (Bybit)
    
    # 充提現功能類別
    deposit_enabled: bool = True              # 充值開關
    withdrawal_enabled: bool = True           # 提現開關
    
    # 費用與限額類別
    withdrawal_fee: float = 0.0               # 基本提現手續費
    extra_withdraw_fee: Optional[float] = None # 額外手續費百分比 (Bitget)
    withdraw_percentage_fee: Optional[float] = None # 手續費百分比 (Bybit)
    min_deposit: Optional[float] = None       # 最小充值額
    min_withdrawal: float = 0.0               # 最小提現額
    max_withdrawal: Optional[float] = None    # 最大提現額 (Binance)
    
    # 合約與瀏覽器類別
    contract_address: Optional[str] = None    # 合約地址 (智能識別核心)
    browser_url: Optional[str] = None         # 區塊瀏覽器URL
    
    # 網路狀態類別
    busy: Optional[bool] = None               # 網路繁忙 (Binance)
    congestion: Optional[str] = None          # 擁堵狀況 (Bitget: normal/congested)
    estimated_arrival_time: Optional[int] = None # 預估到帳時間 (Binance)
    
    # 描述資訊類別
    deposit_desc: Optional[str] = None        # 充值描述 (Binance)
    withdraw_desc: Optional[str] = None       # 提現描述 (Binance)


@dataclass
class SearchableCoinInfo:
    """智能搜索用的幣種資訊 - 只包含重要欄位"""
    # 基本識別類別
    exchange: str                             # 交易所名稱
    symbol: str                               # 幣種符號
    name: str                                 # 幣種名稱
    
    # 網路列表
    networks: List[SearchableNetworkInfo] = field(default_factory=list)


@dataclass
class TransferResult:
    """轉帳結果"""
    transfer_id: str
    status: str  # pending, processing, completed, failed
    tx_hash: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class AccountConfig:
    """帳號配置"""
    name: str
    api_key: str
    secret: str
    passphrase: Optional[str] = None
    testnet: bool = False


class BaseExchange(ABC):
    """交易所基底抽象類別"""
    
    def __init__(self, account_config: Optional[AccountConfig] = None):
        self.account_config = account_config
        self.exchange_name = self.__class__.__name__.replace('Exchange', '').lower()
    
    # 公開端點 - 不需認證
    @abstractmethod
    async def get_supported_currencies(self) -> List[str]:
        """獲取支援的幣種列表"""
        pass
    
    @abstractmethod
    async def get_currency_networks(self, currency: str) -> List[NetworkInfo]:
        """獲取指定幣種支援的網路資訊"""
        pass
    
    @abstractmethod
    async def get_all_coins_info(self) -> List[CoinInfo]:
        """獲取所有幣種的完整資訊（包含所有網路）
        
        這個方法應該返回交易所支援的所有幣種及其網路資訊，
        相當於一次性獲取所有資料，而不需要逐個查詢特定幣種。
        
        Returns:
            List[CoinInfo]: 所有幣種的完整資訊列表
        """
        pass
    
    # 私有端點 - 需認證
    @abstractmethod
    async def get_deposit_address(self, currency: str, network: str) -> str:
        """獲取入金地址"""
        pass
    @abstractmethod
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, float]:
        """查詢餘額"""
        pass
    
    @abstractmethod
    async def withdraw(
        self, 
        currency: str, 
        amount: float, 
        address: str, 
        network: str,
        memo: Optional[str] = None
    ) -> TransferResult:
        """執行出金"""
        pass
    
    @abstractmethod
    async def get_transfer_status(self, transfer_id: str) -> TransferResult:
        """查詢轉帳狀態"""
        pass
    
    @abstractmethod
    async def get_withdrawal_history(
        self, 
        currency: Optional[str] = None, 
        limit: int = 50
    ) -> List[Dict]:
        """查詢出金歷史"""
        pass
    
    def requires_auth(self) -> bool:
        """檢查是否已設定認證資訊"""
        return self.account_config is not None
    
    def _ensure_auth(self):
        """確保已設定認證資訊"""
        if not self.requires_auth():
            raise ValueError(f"需要設定 {self.exchange_name} 的 API 認證資訊")


class ExchangeFactory:
    """交易所工廠類別"""
    
    _exchanges = {}
    
    @classmethod
    def register(cls, name: str, exchange_class):
        """註冊交易所類別"""
        cls._exchanges[name.lower()] = exchange_class
    
    @classmethod
    def create(cls, name: str, account_config: Optional[AccountConfig] = None) -> BaseExchange:
        """創建交易所實例"""
        exchange_class = cls._exchanges.get(name.lower())
        if not exchange_class:
            raise ValueError(f"不支援的交易所: {name}")
        return exchange_class(account_config)
    
    @classmethod
    def get_supported_exchanges(cls) -> List[str]:
        """獲取支援的交易所列表"""
        return list(cls._exchanges.keys())