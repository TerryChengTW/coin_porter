"""
簡單的日誌工具模組
提供統一的日誌記錄功能，支援不同輸出目標
"""

import logging
import os
import inspect
from datetime import datetime
from typing import Optional


class CoinPorterLogger:
    """Coin Porter 專用日誌記錄器"""
    
    def __init__(self):
        self.file_logger = None
        self.console_logger = None
        self.ui_callback = None
        self._setup_loggers()
    
    def _setup_loggers(self):
        """設定日誌記錄器"""
        # 建立 logs 資料夾
        os.makedirs('logs', exist_ok=True)
        
        # 按日期和開啟時間命名檔案
        startup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"logs/coin_porter_{startup_time}.log"
        
        # 檔案 logger（所有級別）
        self.file_logger = logging.getLogger('coin_porter_file')
        self.file_logger.setLevel(logging.DEBUG)
        if not self.file_logger.handlers:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                fmt='[%(asctime)s] %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.file_logger.addHandler(file_handler)
        
        # 控制台 logger（只有 DEBUG）
        self.console_logger = logging.getLogger('coin_porter_console')
        self.console_logger.setLevel(logging.DEBUG)
        if not self.console_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                fmt='[%(asctime)s] DEBUG - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.console_logger.addHandler(console_handler)
    
    def set_ui_callback(self, callback):
        """設定 UI 回呼函數（用於 INFO/ERROR）"""
        self.ui_callback = callback
    
    def _get_caller_info(self):
        """獲取調用者資訊"""
        frame = inspect.currentframe()
        try:
            # 往上找兩層：當前方法 -> log_xxx 函數 -> 實際調用位置
            caller_frame = frame.f_back.f_back.f_back
            filename = os.path.basename(caller_frame.f_code.co_filename)
            lineno = caller_frame.f_lineno
            return f"{filename}:{lineno}"
        except:
            return "unknown:0"
        finally:
            del frame
    
    def info(self, message: str):
        """記錄資訊訊息 - 檔案 + UI"""
        caller_info = self._get_caller_info()
        # 寫入檔案
        self.file_logger.info(f"{caller_info} - {message}")
        # 顯示在 UI
        if self.ui_callback:
            self.ui_callback(f"ℹ️ {message}")
    
    def error(self, message: str):
        """記錄錯誤訊息 - 檔案 + UI"""
        caller_info = self._get_caller_info()
        # 寫入檔案
        self.file_logger.error(f"{caller_info} - {message}")
        # 顯示在 UI
        if self.ui_callback:
            self.ui_callback(f"❌ {message}")
    
    def debug(self, message: str):
        """記錄除錯訊息 - 檔案 + 終端機"""
        caller_info = self._get_caller_info()
        # 寫入檔案
        self.file_logger.debug(f"{caller_info} - {message}")
        # 顯示在終端機
        self.console_logger.debug(f"{caller_info} - {message}")


# 全域 logger 實例
logger = CoinPorterLogger()


def set_ui_log_callback(callback):
    """設定 UI 日誌回呼函數"""
    logger.set_ui_callback(callback)


def log_info(message: str):
    """記錄資訊訊息"""
    logger.info(message)


def log_error(message: str):
    """記錄錯誤訊息"""
    logger.error(message)


def log_debug(message: str):
    """記錄除錯訊息"""
    logger.debug(message)