"""
測試動態合約映射載入功能
"""

import sys
from pathlib import Path

# 添加源碼路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.currency.coin_identifier import CoinIdentifier


def test_dynamic_mapping():
    """測試動態映射載入"""
    print("=== 測試動態合約映射載入功能 ===")
    
    try:
        # 創建識別器
        identifier = CoinIdentifier()
        print("[成功] CoinIdentifier 初始化成功")
        
        # 測試獲取可能的符號
        test_symbols = ["BABYDOGE", "1MBABYDOGE", "CAT", "1000CAT"]
        
        for symbol in test_symbols:
            print(f"\n--- 測試符號: {symbol} ---")
            possible_symbols = identifier.get_possible_symbols(symbol)
            print(f"可能的符號: {possible_symbols}")
            
            # 檢查合約地址
            contracts = identifier.contract_db.find_contracts_by_symbol(symbol)
            if contracts:
                print(f"合約地址: {contracts}")
            else:
                print("未找到合約地址")
        
        # 測試映射配置
        print(f"\n--- 測試映射配置 ---")
        mappings = identifier._get_contract_mappings()
        print(f"載入的映射數量: {len(mappings)}")
        
        for i, mapping in enumerate(mappings[:3]):  # 只顯示前3個
            print(f"映射 {i+1}:")
            print(f"  合約: {mapping['contract']}")
            print(f"  網路: {mapping['network']}")
            print(f"  變體: {mapping['variants']}")
        
        print("\n[成功] 動態映射載入測試完成！")
        
    except Exception as e:
        print(f"[錯誤] 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_dynamic_mapping()