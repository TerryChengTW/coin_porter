#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
sys.path.append('src')

from core.exchanges.manager import ExchangeManager
from core.config.api_keys import APIKeyManager

async def test_babydoge_debug():
    """測試 BABYDOGE 的 denomination 問題"""
    api_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_manager)
    
    print('[測試] 開始獲取所有交易所數據...')
    
    try:
        raw_data, searchable_data = await exchange_manager.get_all_coins_data()
        print(f'獲取到交易所: {list(searchable_data.keys())}')
        
        # 檢查 Binance 是否有 BABYDOGE 相關幣種
        if 'binance' in searchable_data:
            binance_coins = searchable_data['binance']
            babydoge_coins = [coin for coin in binance_coins if 'BABYDOGE' in coin.symbol.upper()]
            print(f'[Binance] BABYDOGE 相關幣種: {len(babydoge_coins)} 個')
            
            for coin in babydoge_coins:
                print(f'  - {coin.symbol} (name: {coin.name}, denomination: {coin.denomination})')
                if coin.denomination:
                    # 測試去掉前綴後的名稱
                    if coin.symbol.startswith(str(coin.denomination)):
                        base_symbol = coin.symbol[len(str(coin.denomination)):]
                        print(f'    去掉前綴後: {base_symbol}')
                    # 如果是 1M 這種格式
                    elif coin.symbol.startswith('1M'):
                        base_symbol = coin.symbol[2:]  # 去掉 "1M"
                        print(f'    去掉 1M 前綴後: {base_symbol}')
                
                for network in coin.networks:
                    if network.contract_address:
                        print(f'    網路: {network.network}, 合約: {network.contract_address}')
        
        # 測試傳統搜索
        print('\n[測試] 執行 BABYDOGE 傳統搜索...')
        traditional_results = exchange_manager._search_from_cached_data('BABYDOGE', searchable_data)
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
    asyncio.run(test_babydoge_debug())