#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from src.core.config.api_keys import APIKeyManager
from src.core.exchanges.manager import ExchangeManager
from src.core.currency.coin_identifier import NetworkStandardizer

async def test_smart_search_logic():
    """測試智能搜索邏輯，專門調試 1000CAT 和 CAT 的問題"""
    
    print("[測試] 開始智能搜索邏輯測試...")
    
    # 初始化管理器
    api_key_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_key_manager)
    
    # 獲取所有幣種數據
    print("[測試] 獲取所有幣種數據...")
    raw_data_by_exchange, searchable_data_by_exchange = await exchange_manager.get_all_coins_data()
    
    # 測試網路標準化器
    network_standardizer = NetworkStandardizer()
    
    print("\n[DEBUG] 測試網路標準化:")
    test_networks = ["BSC", "BEP20", "SOL", "Solana", "BTC", "Bitcoin"]
    for net in test_networks:
        std_net = network_standardizer.standardize_network(net)
        print(f"  {net} -> {std_net}")
    
    # 查找 1000CAT 和 CAT 的資料
    print("\n[DEBUG] 分析 1000CAT 和 CAT 在各交易所的資料:")
    
    for exchange_name, coins in searchable_data_by_exchange.items():
        print(f"\n--- {exchange_name.upper()} ---")
        
        # 查找 1000CAT
        for coin in coins:
            if coin.symbol.upper() in ["1000CAT", "CAT"]:
                print(f"找到 {coin.symbol}:")
                for network in coin.networks:
                    std_network = network_standardizer.standardize_network(network.network)
                    print(f"  網路: {network.network} -> 標準化: {std_network}")
                    print(f"  合約地址: {network.contract_address}")
                    if network.contract_address:
                        contract_key = f"{network.contract_address.lower()}_{std_network}"
                        print(f"  合約鍵: {contract_key}")
                    print()
    
    # 模擬智能搜索過程
    print("\n[DEBUG] 模擬智能搜索 '1000CAT' 的過程:")
    
    # 第一步：收集所有合約地址映射
    contract_map = {}
    for exchange_name, coins in searchable_data_by_exchange.items():
        for coin in coins:
            for network in coin.networks:
                if network.contract_address:
                    std_network = network_standardizer.standardize_network(network.network)
                    contract_key = f"{network.contract_address.lower()}_{std_network}"
                    if contract_key not in contract_map:
                        contract_map[contract_key] = []
                    contract_map[contract_key].append((exchange_name, coin.symbol, network.network))
    
    # 第二步：找出 1000CAT 相關的合約地址
    input_contracts = set()
    for exchange_name, coins in searchable_data_by_exchange.items():
        for coin in coins:
            if coin.symbol.upper() == "1000CAT":
                for network in coin.networks:
                    if network.contract_address:
                        std_network = network_standardizer.standardize_network(network.network)
                        contract_key = f"{network.contract_address.lower()}_{std_network}"
                        input_contracts.add(contract_key)
                        print(f"找到 1000CAT 的合約鍵: {contract_key} ({exchange_name}, 網路: {network.network})")
    
    print(f"\n1000CAT 總共有 {len(input_contracts)} 個合約鍵")
    
    # 第三步：查找所有使用相同合約的幣種
    print(f"\n[DEBUG] 查找使用相同合約地址的所有幣種:")
    for contract_key in input_contracts:
        if contract_key in contract_map:
            entries = contract_map[contract_key]
            print(f"\n合約鍵 {contract_key} 的所有變體:")
            for exchange, symbol, original_network in entries:
                print(f"  - {exchange}: {symbol} ({original_network})")
        else:
            print(f"\n合約鍵 {contract_key} 沒有找到匹配的變體")
    
    # 測試搜索 CAT 的情況
    print(f"\n\n[DEBUG] 模擬智能搜索 'CAT' 的過程:")
    
    # 找出 CAT 相關的合約地址
    cat_input_contracts = set()
    for exchange_name, coins in searchable_data_by_exchange.items():
        for coin in coins:
            if coin.symbol.upper() == "CAT":
                for network in coin.networks:
                    if network.contract_address:
                        std_network = network_standardizer.standardize_network(network.network)
                        contract_key = f"{network.contract_address.lower()}_{std_network}"
                        cat_input_contracts.add(contract_key)
                        print(f"找到 CAT 的合約鍵: {contract_key} ({exchange_name}, 網路: {network.network})")
    
    print(f"\nCAT 總共有 {len(cat_input_contracts)} 個合約鍵")
    
    # 查找所有使用相同合約的幣種
    print(f"\n[DEBUG] 查找使用相同合約地址的所有幣種:")
    for contract_key in cat_input_contracts:
        if contract_key in contract_map:
            entries = contract_map[contract_key]
            print(f"\n合約鍵 {contract_key} 的所有變體:")
            for exchange, symbol, original_network in entries:
                print(f"  - {exchange}: {symbol} ({original_network})")
        else:
            print(f"\n合約鍵 {contract_key} 沒有找到匹配的變體")

if __name__ == "__main__":
    asyncio.run(test_smart_search_logic())