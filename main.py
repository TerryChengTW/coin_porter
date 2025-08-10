#!/usr/bin/env python3
"""
Coin Porter - 跨交易所資金轉移工具

主程式入口，提供基本的測試和演示功能
"""

import asyncio
import json
from src.core.config.api_keys import APIKeyManager
from src.core.exchanges.manager import ExchangeManager


async def test_currency_support():
    """測試幣種支援查詢功能"""
    print("=== Coin Porter Test Program ===")
    
    # 載入配置
    try:
        api_manager = APIKeyManager()
        exchange_manager = ExchangeManager(api_manager)
        
        print(f"Enabled exchanges: {api_manager.get_enabled_exchanges()}")
        print(f"Queryable exchanges: {api_manager.get_queryable_exchanges()}")
        print(f"Configured accounts: {api_manager.get_all_accounts()}")
        print()
        
        # 測試查詢 BTC 支援情況
        print("Querying BTC support...")
        btc_support = await exchange_manager.query_currency_support("BTC")
        
        for exchange, networks in btc_support.items():
            print(f"\n{exchange.upper()}:")
            if networks:
                for network in networks:
                    status = "[OK]" if network.deposit_enabled and network.withdrawal_enabled else "[X]"
                    print(f"  {status} {network.network}: Min {network.min_withdrawal}, Fee {network.withdrawal_fee}")
            else:
                print("  [No support or query failed]")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")


async def test_all_currencies():
    """測試獲取所有支援幣種"""
    print("\n=== Query All Supported Currencies ===")
    
    try:
        api_manager = APIKeyManager()
        exchange_manager = ExchangeManager(api_manager)
        
        all_currencies = await exchange_manager.get_all_supported_currencies()
        
        for exchange, currencies in all_currencies.items():
            print(f"\n{exchange.upper()}: {len(currencies)} currencies")
            if currencies:
                # 只顯示前 10 個作為範例
                preview = currencies[:10]
                print(f"  Examples: {', '.join(preview)}")
                if len(currencies) > 10:
                    print(f"  ... and {len(currencies) - 10} more")
            else:
                print("  [No data or query failed]")
                
    except Exception as e:
        print(f"[ERROR] {str(e)}")


def main():
    """主函式"""
    print("Coin Porter v1.0.0")
    print("Cross-exchange transfer tool\n")
    
    # 檢查配置檔案
    if not os.path.exists("api_keys.json"):
        print("[WARNING] api_keys.json config file not found")
        print("Please setup API key configuration")
        return
    
    try:
        # 執行測試
        asyncio.run(test_currency_support())
        asyncio.run(test_all_currencies())
        
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    except Exception as e:
        print(f"[CRITICAL ERROR] {str(e)}")


if __name__ == "__main__":
    import os
    main()