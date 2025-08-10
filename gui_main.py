#!/usr/bin/env python3
"""
Coin Porter GUI 主程式
跨交易所加密貨幣轉帳工具的圖形化介面
"""

import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.main_window import main

if __name__ == "__main__":
    sys.exit(main())