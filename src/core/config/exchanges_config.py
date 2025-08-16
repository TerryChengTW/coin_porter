"""
交易所配置管理器
"""

import json
import importlib
from typing import Dict, List, Type, Optional
from pathlib import Path
from ..utils.logger import log_error


class ExchangeConfig:
    """交易所配置類別"""
    
    def __init__(self, config_data: dict):
        self.name = config_data['name']
        self.display_name = config_data['display_name']
        self.class_name = config_data['class_name']
        self.module = config_data['module']
        self.supports_public_query = config_data.get('supports_public_query', False)
        self.enabled = config_data.get('enabled', True)


class ExchangeConfigManager:
    """交易所配置管理器"""
    
    def __init__(self, config_file: str = "exchanges_config.json"):
        self.config_file = Path(config_file)
        self._exchanges: Dict[str, ExchangeConfig] = {}
        self._exchange_classes: Dict[str, Type] = {}
        self._load_config()
    
    def _load_config(self):
        """載入交易所配置"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Exchange config file not found: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        for exchange_data in config_data['supported_exchanges']:
            exchange_config = ExchangeConfig(exchange_data)
            self._exchanges[exchange_config.name] = exchange_config
            
            # 動態載入交易所類別
            if exchange_config.enabled:
                self._load_exchange_class(exchange_config)
    
    def _load_exchange_class(self, config: ExchangeConfig):
        """動態載入交易所類別"""
        try:
            module = importlib.import_module(config.module)
            exchange_class = getattr(module, config.class_name)
            self._exchange_classes[config.name] = exchange_class
        except (ImportError, AttributeError) as e:
            log_error(f"無法載入交易所 {config.name}: {e}")
    
    def get_enabled_exchanges(self) -> List[str]:
        """獲取啟用的交易所名稱列表"""
        return [name for name, config in self._exchanges.items() if config.enabled]
    
    
    def get_exchange_names(self) -> List[str]:
        """獲取交易所名稱列表"""
        return [name for name, config in self._exchanges.items() if config.enabled]
    
    def get_exchange_class(self, name: str) -> Optional[Type]:
        """獲取指定交易所的類別"""
        return self._exchange_classes.get(name)
    
    def supports_public_query(self, name: str) -> bool:
        """檢查交易所是否支援公開查詢"""
        config = self._exchanges.get(name)
        return config.supports_public_query if config else False
    
    def is_exchange_enabled(self, name: str) -> bool:
        """檢查交易所是否啟用"""
        config = self._exchanges.get(name)
        return config.enabled if config else False
