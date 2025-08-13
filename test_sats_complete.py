#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
sys.path.append('src')

from core.exchanges.manager import ExchangeManager
from core.config.api_keys import APIKeyManager

async def test_sats_complete():
    """測試完整的 SATS 智能識別流程"""
    api_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_manager)
    
    print('[測試] 執行完整的 SATS 智能識別...')
    
    try:
        result, searchable_data = await exchange_manager.enhanced_currency_query('SATS')
        
        print(f'\n[結果] 原始符號: {result.original_symbol}')
        print(f'[結果] 驗證匹配: {len(result.verified_matches)} 個')
        print(f'[結果] 可能匹配: {len(result.possible_matches)} 個')
        
        print('\n=== 驗證匹配詳情 ===')
        for i, match in enumerate(result.verified_matches):
            print(f'{i+1}. {match.exchange} - {match.symbol}')
            print(f'   網路: {match.network}')
            print(f'   合約: {match.contract_address}')
            print()
        
        if result.possible_matches:
            print('\n=== 可能匹配詳情 ===')
            for i, match in enumerate(result.possible_matches):
                print(f'{i+1}. {match.exchange} - {match.symbol}')
                print(f'   網路: {match.network}')
                print(f'   合約: {match.contract_address}')
                print()
        
        # 檢查是否找到了 1000SATS
        binance_matches = [m for m in result.verified_matches if m.exchange == 'binance']
        if binance_matches:
            print(f'[成功] 找到 Binance 匹配: {len(binance_matches)} 個')
            for match in binance_matches:
                print(f'  - {match.symbol} (網路: {match.network})')
        else:
            print('[問題] 沒有找到 Binance 匹配')
                
    except Exception as e:
        import traceback
        print(f'[錯誤] {e}')
        print(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(test_sats_complete())