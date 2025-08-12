"""
測試完整的智能識別流程
"""

import sys
import asyncio
from pathlib import Path

# 添加源碼路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.exchanges.manager import ExchangeManager
from src.core.config.api_keys import APIKeyManager


async def test_enhanced_query():
    """測試增強查詢功能"""
    print("=== 測試增強的幣種查詢功能 ===")
    
    try:
        # 初始化管理器
        api_manager = APIKeyManager()
        exchange_manager = ExchangeManager(api_manager)
        
        # 測試 babydoge
        print("\n--- 測試查詢: babydoge ---")
        result = await exchange_manager.enhanced_currency_query("babydoge")
        
        if result:
            print(f"原始符號: {result.original_symbol}")
            print(f"驗證匹配數量: {len(result.verified_matches)}")
            print(f"可能匹配數量: {len(result.possible_matches)}")
            
            print("\n驗證匹配:")
            for match in result.verified_matches:
                print(f"  - {match.exchange}: {match.symbol} ({match.network}) - {match.contract_address}")
            
            print("\n可能匹配:")
            for match in result.possible_matches:
                print(f"  - {match.exchange}: {match.symbol} ({match.network}) - {match.contract_address}")
            
            if result.debug_info:
                print(f"\n除錯資訊: {len(result.debug_info)} 個")
                for debug in result.debug_info[:3]:  # 只顯示前3個
                    print(f"  - {debug}")
        else:
            print("未找到結果")
        
        print("\n[成功] 增強查詢測試完成！")
        
    except Exception as e:
        print(f"[錯誤] 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhanced_query())