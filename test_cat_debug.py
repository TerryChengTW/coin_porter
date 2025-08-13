#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import time
sys.path.append('src')

from core.exchanges.manager import ExchangeManager
from core.config.api_keys import APIKeyManager

async def test_cat_debug():
    """測試 CAT 智能識別的詳細過程"""
    api_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_manager)
    
    print('[測試] 開始獲取所有交易所數據...')
    start_time = time.time()
    
    try:
        raw_data, searchable_data = await asyncio.wait_for(
            exchange_manager.get_all_coins_data(), 
            timeout=60.0  # 60秒超時
        )
        get_data_time = time.time() - start_time
        print(f'[成功] 獲取數據完成，耗時 {get_data_time:.2f} 秒')
        print(f'獲取到交易所: {list(searchable_data.keys())}')
        
        # 檢查是否有 CAT 相關的幣種
        cat_found = {}
        for exchange, coins in searchable_data.items():
            cat_coins = [coin for coin in coins if 'CAT' in coin.symbol.upper()]
            if cat_coins:
                cat_found[exchange] = [coin.symbol for coin in cat_coins]
        
        print(f'[發現] CAT 相關幣種: {cat_found}')
        
        # 測試傳統搜索
        print('[測試] 執行傳統搜索...')
        traditional_start = time.time()
        traditional_results = exchange_manager._search_from_cached_data('CAT', searchable_data)
        traditional_time = time.time() - traditional_start
        print(f'[結果] 傳統搜索完成，耗時 {traditional_time:.3f} 秒')
        print(f'傳統搜索結果: {traditional_results}')
        
        # 測試智能識別
        print('[測試] 執行智能識別...')
        smart_start = time.time()
        
        try:
            smart_results = await asyncio.wait_for(
                asyncio.create_task(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        exchange_manager._smart_identification_from_cached_data, 
                        'CAT', 
                        searchable_data
                    )
                ), 
                timeout=30.0  # 30秒超時
            )
            smart_time = time.time() - smart_start
            print(f'[成功] 智能識別完成，耗時 {smart_time:.3f} 秒')
            print(f'智能識別找到 {len(smart_results)} 個結果')
            
        except asyncio.TimeoutError:
            print('[超時] 智能識別超過30秒，可能卡住了')
            return
        
        # 顯示前幾個結果
        for i, result in enumerate(smart_results[:10]):
            print(f'  {i+1}: {result.exchange} - {result.symbol} ({result.network})')
            
    except asyncio.TimeoutError:
        print('[超時] 獲取數據超過60秒')
    except Exception as e:
        import traceback
        print(f'[錯誤] {e}')
        print(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(test_cat_debug())