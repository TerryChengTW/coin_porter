#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from src.core.config.api_keys import APIKeyManager
from src.core.exchanges.manager import ExchangeManager

async def test_fixed_smart_search():
    """測試修復後的智能搜索"""
    
    print("[測試] 測試修復後的智能搜索...")
    
    # 初始化管理器
    api_key_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_key_manager)
    
    # 測試搜索 CAT
    print("\n[測試] 搜索 'CAT'...")
    result, _ = await exchange_manager.enhanced_currency_query("CAT")
    
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
    
    # 驗證 SOL 網路是否出現
    has_sol = any(match.network.upper() == "SOL" for match in result.verified_matches)
    print(f"\n[驗證] SOL 網路是否出現: {'是' if has_sol else '否'}")
    
    # 顯示包含的所有網路
    networks = set(match.network.upper() for match in result.verified_matches)
    print(f"[驗證] 包含的網路: {sorted(networks)}")

if __name__ == "__main__":
    asyncio.run(test_fixed_smart_search())