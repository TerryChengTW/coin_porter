#!/usr/bin/env python3
"""
測試6個具體的名稱不同但實際相同的幣種案例
"""

import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.currency.coin_identifier import CoinIdentifier


def test_specific_cases():
    """測試6個具體案例"""
    print("=== 測試6個具體的幣種案例 ===\n")
    
    identifier = CoinIdentifier()
    
    # 定義測試案例
    test_cases = [
        {
            "name": "1MBABYDOGE vs BABYDOGE",
            "contract": "0xc748673057861a797275cd8a068abb95a902e8de",
            "network": "BSC",
            "symbols": ["1MBABYDOGE", "BABYDOGE"],
            "exchanges": {"1MBABYDOGE": ["binance"], "BABYDOGE": ["bybit"]}
        },
        {
            "name": "BEAMX vs BEAM", 
            "contract": "0x62d0a8458ed7719fdaf978fe5929c6d342b0bfce",
            "network": "ETH",
            "symbols": ["BEAMX", "BEAM"],
            "exchanges": {"BEAMX": ["binance"], "BEAM": ["bybit"]}
        },
        {
            "name": "1000CAT vs CAT",
            "contract": "0x6894cde390a3f51155ea41ed24a33a4827d3063d", 
            "network": "BSC",
            "symbols": ["1000CAT", "CAT"],
            "exchanges": {"1000CAT": ["binance"], "CAT": ["bybit"]}
        },
        {
            "name": "BTTC vs BTT",
            "contract": "TAFjULxiVgT4qWk6UZwjqwZXTSaGaqnVp4",
            "network": "TRX",
            "symbols": ["BTTC", "BTT"],
            "exchanges": {"BTTC": ["binance"], "BTT": ["bybit"]}
        },
        {
            "name": "NEIRO vs NEIROCTO",
            "contract": "0x812ba41e071c7b7fa4ebcfb62df5f45f6fa853ee",
            "network": "ETH", 
            "symbols": ["NEIRO", "NEIROCTO"],
            "exchanges": {"NEIRO": ["binance"], "NEIROCTO": ["bybit"]}
        },
        {
            "name": "ZEROLEND vs ZERO",
            "contract": "0x78354f8dccb269a615a7e0a24f9b0718fdc3c7a7",
            "network": "LINEA",
            "symbols": ["ZEROLEND", "ZERO"], 
            "exchanges": {"ZEROLEND": ["bitget"], "ZERO": ["bybit"]}
        }
    ]
    
    # 測試每個案例
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
        print(f"   合約: {case['contract']}")
        print(f"   網路: {case['network']}")
        
        # 測試每個符號能否找到對應的別名
        for symbol in case['symbols']:
            possible_symbols = identifier.get_possible_symbols(symbol)
            expected_symbols = set(case['symbols'])
            
            if expected_symbols.issubset(possible_symbols):
                print(f"   ✅ {symbol} -> 找到別名: {possible_symbols}")
            else:
                print(f"   ❌ {symbol} -> 只找到: {possible_symbols}, 期望: {expected_symbols}")
        
        # 測試合約地址映射
        db = identifier.contract_db
        contract_symbols = db.get_all_symbols_for_contract(case['contract'])
        std_network = identifier.network_standardizer.standardize_network(case['network'])
        
        if std_network in contract_symbols:
            stored_symbol = contract_symbols[std_network]
            if stored_symbol in case['symbols']:
                print(f"   ✅ 合約地址映射正確: {stored_symbol}")
            else:
                print(f"   ❌ 合約地址映射錯誤: 儲存了 {stored_symbol}, 期望 {case['symbols']} 之一")
        else:
            print(f"   ❌ 合約地址未找到映射")
        
        print()


def test_reverse_lookup():
    """測試反向查詢 - 從合約地址找符號"""
    print("=== 測試反向查詢 ===\n")
    
    identifier = CoinIdentifier()
    
    test_contracts = [
        ("0x6894cde390a3f51155ea41ed24a33a4827d3063d", "BSC", ["CAT", "1000CAT"]),
        ("sats", "BRC20", ["SATS", "1000SATS"]),
        ("0xc748673057861a797275cd8a068abb95a902e8de", "BSC", ["BABYDOGE", "1MBABYDOGE"]),
    ]
    
    for contract, network, expected_symbols in test_contracts:
        found_symbols = identifier.contract_db.find_symbols_by_contract(contract, network)
        print(f"合約 {contract[:20]}... 在 {network}")
        print(f"  找到: {found_symbols}")
        print(f"  期望: {expected_symbols}")
        
        if any(symbol in expected_symbols for symbol in found_symbols):
            print("  ✅ 反向查詢成功")
        else:
            print("  ❌ 反向查詢失敗")
        print()


def test_network_standardization():
    """測試網路標準化對這些案例的影響"""
    print("=== 測試網路標準化 ===\n")
    
    identifier = CoinIdentifier()
    standardizer = identifier.network_standardizer
    
    # 測試這些案例用到的網路
    test_networks = [
        ("BSC", ["BSC", "BEP20", "BNB Smart Chain"]),
        ("ETH", ["ETH", "ERC20", "Ethereum"]),
        ("TRX", ["TRX", "TRC20", "Tron"]),
        ("LINEA", ["LINEA"]),
        ("BRC20", ["BRC20", "ORDIBTC"])
    ]
    
    for standard, variants in test_networks:
        print(f"標準網路: {standard}")
        for variant in variants:
            result = standardizer.standardize_network(variant)
            status = "✅" if result == standard else "❌"
            print(f"  {status} {variant} -> {result}")
        print()


def main():
    """主測試函數"""
    print("開始測試6個具體的幣種案例...\n")
    
    try:
        test_specific_cases()
        test_reverse_lookup()
        test_network_standardization()
        
        print("✅ 所有測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()