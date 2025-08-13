#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import time
sys.path.append('src')

from core.exchanges.manager import ExchangeManager
from core.config.api_keys import APIKeyManager

async def test_sats_debug():
    """測試 SATS 搜索問題"""
    api_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_manager)
    
    print('[測試] 開始獲取所有交易所數據...')
    
    try:
        raw_data, searchable_data = await exchange_manager.get_all_coins_data()
        print(f'獲取到交易所: {list(searchable_data.keys())}')
        
        # 檢查 Binance 是否有 SATS 相關幣種
        if 'binance' in searchable_data:
            binance_coins = searchable_data['binance']
            sats_coins = [coin for coin in binance_coins if 'SATS' in coin.symbol.upper()]
            print(f'[Binance] SATS 相關幣種: {len(sats_coins)} 個')
            
            for coin in sats_coins:
                print(f'  - {coin.symbol} (name: {coin.name}, denomination: {coin.denomination})')
                for network in coin.networks:
                    if network.contract_address:
                        print(f'    網路: {network.network}, 合約: {network.contract_address}')
        
        # 檢查其他交易所的 SATS
        for exchange_name, coins in searchable_data.items():
            if exchange_name != 'binance':
                sats_coins = [coin for coin in coins if coin.symbol.upper() == 'SATS']
                if sats_coins:
                    print(f'[{exchange_name}] 找到 SATS: {len(sats_coins)} 個')
                    for coin in sats_coins:
                        for network in coin.networks:
                            if network.contract_address:
                                print(f'  網路: {network.network}, 合約: {network.contract_address}')
        
        # 測試傳統搜索
        print('\n[測試] 執行 SATS 傳統搜索...')
        traditional_results = exchange_manager._search_from_cached_data('SATS', searchable_data)
        for exchange, networks in traditional_results.items():
            if networks:
                print(f'[傳統搜索] {exchange}: 找到 {len(networks)} 個網路')
                for net in networks:
                    print(f'  - {net.network} (合約: {net.contract_address})')
            else:
                print(f'[傳統搜索] {exchange}: 無結果')
                
    except Exception as e:
        import traceback
        print(f'[錯誤] {e}')
        print(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(test_sats_debug())