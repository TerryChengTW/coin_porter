#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from src.core.config.api_keys import APIKeyManager
from src.core.exchanges.manager import ExchangeManager

async def test_1000cat_search():
    """測試搜索 1000CAT 的情況"""
    
    print("[測試] 測試搜索 '1000CAT'...")
    
    # 初始化管理器
    api_key_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_key_manager)
    
    # 測試搜索 1000CAT
    print("\n[測試] 搜索 '1000CAT'...")
    result, _ = await exchange_manager.enhanced_currency_query("1000CAT")
    
    print(f"\n[結果] 找到 {len(result.verified_matches)} 個驗證匹配:")
    
    # 按交易所和網路分組顯示結果
    by_exchange_network = {}
    for match in result.verified_matches:
        key = f"{match.exchange}-{match.network}"
        if key not in by_exchange_network:
            by_exchange_network[key] = []
        by_exchange_network[key].append(match)
    
    for key in sorted(by_exchange_network.keys()):
        matches = by_exchange_network[key]
        exchange, network = key.split('-', 1)
        print(f"  {exchange.upper()} {network}:")
        for match in matches:
            print(f"    - {match.symbol} (合約: {match.contract_address[:10] if match.contract_address else '無'}...)")
    
    # 驗證結果
    has_binance_sol = any(match.exchange == "binance" and match.network == "SOL" for match in result.verified_matches)
    has_binance_bsc = any(match.exchange == "binance" and match.network == "BSC" for match in result.verified_matches)
    has_bybit_bsc = any(match.exchange == "bybit" and match.network == "BSC" for match in result.verified_matches)
    
    print(f"\n[驗證] Binance SOL: {'是' if has_binance_sol else '否'}")
    print(f"[驗證] Binance BSC: {'是' if has_binance_bsc else '否'}")
    print(f"[驗證] Bybit BSC: {'是' if has_bybit_bsc else '否'}")
    
    # 顯示包含的所有網路
    networks = set(match.network.upper() for match in result.verified_matches)
    print(f"[驗證] 包含的網路: {sorted(networks)}")

if __name__ == "__main__":
    asyncio.run(test_1000cat_search())