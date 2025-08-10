import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from ..exchanges.base import AccountConfig


class APIKeyManager:
    """API 金鑰管理器"""
    
    def __init__(self, config_file: str = "api_config.json"):
        self.config_file = config_file
        self._config = self._load_config()
        
        # 確保配置結構
        if "enabled_exchanges" not in self._config:
            self._config["enabled_exchanges"] = ["binance", "bybit", "bitget"]  # 默認全部
        if "accounts" not in self._config:
            self._config["accounts"] = {}
    
    def _load_config(self) -> Dict:
        """載入配置檔案"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_config(self):
        """儲存配置到檔案"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def add_account(self, exchange: str, account_name: str, account_config: AccountConfig):
        """新增帳號配置"""
        if exchange not in self._config["accounts"]:
            self._config["accounts"][exchange] = {}
        
        self._config["accounts"][exchange][account_name] = {
            "api_key": account_config.api_key,
            "secret": account_config.secret,
            "passphrase": account_config.passphrase,
            "testnet": account_config.testnet
        }
        self.save_config()
    
    def remove_account(self, exchange: str, account_name: str):
        """移除帳號配置"""
        accounts = self._config.get("accounts", {})
        if exchange in accounts and account_name in accounts[exchange]:
            del accounts[exchange][account_name]
            if not accounts[exchange]:  # 如果該交易所沒有帳號了
                del accounts[exchange]
            self.save_config()
    
    def get_account(self, exchange: str, account_name: str) -> Optional[AccountConfig]:
        """獲取指定帳號配置"""
        accounts = self._config.get("accounts", {})
        if exchange in accounts and account_name in accounts[exchange]:
            config_data = accounts[exchange][account_name]
            return AccountConfig(
                name=account_name,
                api_key=config_data["api_key"],
                secret=config_data["secret"],
                passphrase=config_data.get("passphrase"),
                testnet=config_data.get("testnet", False)
            )
        return None
    
    def get_all_accounts(self) -> Dict[str, List[str]]:
        """獲取所有已配置的帳號
        
        Returns:
            {"binance": ["main", "backup"], "bybit": ["account1"]}
        """
        accounts = self._config.get("accounts", {})
        return {exchange: list(accs.keys()) for exchange, accs in accounts.items()}
    
    def get_exchange_accounts(self, exchange: str) -> List[str]:
        """獲取指定交易所的所有帳號名稱"""
        accounts = self._config.get("accounts", {})
        return list(accounts.get(exchange, {}).keys())
    
    def has_any_account(self) -> bool:
        """檢查是否有任何已配置的帳號"""
        accounts = self._config.get("accounts", {})
        return bool(accounts)
    
    def has_exchange_account(self, exchange: str) -> bool:
        """檢查指定交易所是否有已配置的帳號"""
        accounts = self._config.get("accounts", {})
        return exchange in accounts and bool(accounts[exchange])
    
    # 交易所啟用管理
    def set_enabled_exchanges(self, exchanges: List[str]):
        """設定啟用的交易所列表"""
        self._config["enabled_exchanges"] = exchanges
        self.save_config()
    
    def get_enabled_exchanges(self) -> List[str]:
        """獲取啟用的交易所列表"""
        return self._config.get("enabled_exchanges", ["binance", "bybit", "bitget"])
    
    def is_exchange_enabled(self, exchange: str) -> bool:
        """檢查交易所是否啟用"""
        return exchange in self.get_enabled_exchanges()
    
    def get_queryable_exchanges(self) -> List[str]:
        """獲取可查詢的交易所（啟用且已配置帳號）"""
        enabled = self.get_enabled_exchanges()
        accounts = self._config.get("accounts", {})
        return [ex for ex in enabled if ex in accounts and accounts[ex]]