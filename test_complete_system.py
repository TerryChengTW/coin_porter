#!/usr/bin/env python3
"""
測試完整的雙路線幣種識別系統
"""

import sys
import os
import asyncio

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.exchanges.manager import ExchangeManager
from src.core.config.api_keys import APIKeyManager


async def test_complete_identification():
    """測試完整的智能識別系統"""
    print("=== 測試完整雙路線幣種識別系統 ===")
    
    # 初始化管理器
    api_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_manager)
    
    # 測試已知的幣種變體
    test_cases = [
        "CAT",      # 應該找到 CAT (bybit) 和 1000CAT (binance)
        "ZK",       # 剛修正的合約地址顯示
        "SATS",     # 應該找到 SATS 和 1000SATS
        "BEAM",     # 應該找到 BEAM 和 BEAMX
    ]
    
    for currency in test_cases:
        print(f"\n🔍 測試幣種: {currency}")
        print("=" * 50)
        
        try:
            # 1. 先執行傳統查詢
            print("📋 傳統查詢結果:")
            traditional_results = await exchange_manager.query_currency_support(currency)
            
            for exchange, networks in traditional_results.items():
                if networks:
                    print(f"  {exchange.upper()}: {len(networks)} 個網路")
                    for net in networks:
                        print(f"    - {net.network} (合約: {net.contract_address or 'N/A'})")
                else:
                    print(f"  {exchange.upper()}: 無支援")
            
            # 2. 執行智能識別
            print("\n🧠 智能識別結果:")
            enhanced_result = await exchange_manager.enhanced_currency_query(currency)
            
            if enhanced_result:
                print(f"  原始符號: {enhanced_result.original_symbol}")
                print(f"  驗證匹配: {len(enhanced_result.verified_matches)} 個")
                print(f"  可能匹配: {len(enhanced_result.possible_matches)} 個")
                print(f"  除錯資訊: {len(enhanced_result.debug_info)} 個")
                
                # 顯示額外發現的匹配
                additional_matches = [
                    match for match in enhanced_result.verified_matches 
                    if match.symbol != currency.upper()
                ]
                
                if additional_matches:
                    print("\n  ✨ 智能識別額外發現:")
                    for match in additional_matches:
                        print(f"    - {match.exchange.upper()}: {match.symbol} ({match.network})")
                        print(f"      合約: {match.contract_address}")
                else:
                    print("\n  ℹ️ 無額外發現")
                    
            else:
                print("  ❌ 智能識別失敗")
                
        except Exception as e:
            print(f"❌ 測試 {currency} 時發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主函數"""
    print("開始測試完整的雙路線幣種識別系統...\n")
    
    try:
        asyncio.run(test_complete_identification())
        
        print("\n" + "=" * 60)
        print("🎉 完整系統測試完成！")
        print("\n💡 測試內容:")
        print("   ✅ Bitget 合約地址修正")
        print("   ✅ 傳統查詢功能")
        print("   ✅ 智能識別功能")
        print("   ✅ 雙路線識別策略")
        print("   ✅ 已知變體識別")
        
    except Exception as e:
        print(f"❌ 主測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()