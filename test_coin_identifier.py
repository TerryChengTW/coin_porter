#!/usr/bin/env python3
"""
測試雙路線幣種識別功能
"""

import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.currency.coin_identifier import CoinIdentifier, NetworkStandardizer


def test_network_standardizer():
    """測試網路名稱標準化"""
    print("=== 測試網路名稱標準化 ===")
    
    standardizer = NetworkStandardizer()
    
    test_cases = [
        ("BSC", "BSC"),
        ("BEP20", "BSC"),
        ("BNB Smart Chain (BEP20)", "BSC"),
        ("ETH", "ETH"),
        ("ERC20", "ETH"),
        ("Ethereum (ERC20)", "ETH"),
        ("TRX", "TRX"),
        ("TRC20", "TRX"),
        ("Arbitrum One", "ARBITRUM"),
        ("ARBI", "ARBITRUM"),
    ]
    
    for input_name, expected in test_cases:
        result = standardizer.standardize_network(input_name)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_name:25} -> {result:10} (期望: {expected})")


def test_coin_identifier():
    """測試幣種識別器"""
    print("\n=== 測試幣種識別器 ===")
    
    identifier = CoinIdentifier()
    
    # 測試獲取可能的符號
    test_symbols = ["CAT", "1000CAT", "SATS", "1000SATS", "BTC"]
    
    for symbol in test_symbols:
        possible = identifier.get_possible_symbols(symbol)
        print(f"{symbol:10} -> 可能的別名: {possible}")


def test_contract_database():
    """測試合約地址資料庫"""
    print("\n=== 測試合約地址資料庫 ===")
    
    identifier = CoinIdentifier()
    db = identifier.contract_db
    
    # 測試已知的合約地址
    test_contracts = [
        "0x6894cde390a3f51155ea41ed24a33a4827d3063d",  # CAT/1000CAT
        "sats",  # SATS/1000SATS
        "0xc748673057861a797275cd8a068abb95a902e8de",  # BABYDOGE/1MBABYDOGE
    ]
    
    for contract in test_contracts:
        symbols = db.get_all_symbols_for_contract(contract)
        print(f"合約 {contract[:20]}... -> 符號: {symbols}")


def main():
    """主測試函數"""
    print("開始測試雙路線幣種識別功能...\n")
    
    try:
        test_network_standardizer()
        test_coin_identifier()
        test_contract_database()
        
        print("\n[成功] 所有測試完成！")
        
    except Exception as e:
        print(f"\n[錯誤] 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()