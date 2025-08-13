#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
sys.path.append('src')

from core.exchanges.manager import ExchangeManager
from core.config.api_keys import APIKeyManager

async def test_babydoge_complete():
    """測試完整的 BABYDOGE 智能識別流程"""
    api_manager = APIKeyManager()
    exchange_manager = ExchangeManager(api_manager)
    
    print('[測試] 執行完整的 BABYDOGE 智能識別...')
    
    try:
        result, searchable_data = await exchange_manager.enhanced_currency_query('BABYDOGE')
        
        print(f'\n[結果] 原始符號: {result.original_symbol}')
        print(f'[結果] 驗證匹配: {len(result.verified_matches)} 個')
        print(f'[結果] 可能匹配: {len(result.possible_matches)} 個')
        
        print('\n=== 驗證匹配詳情 ===')
        for i, match in enumerate(result.verified_matches):
            print(f'{i+1}. {match.exchange} - {match.symbol}')
            print(f'   網路: {match.network}')
            print(f'   合約: {match.contract_address}')
            print()
        
        # 統計各交易所的匹配
        exchange_counts = {}
        for match in result.verified_matches:
            if match.exchange not in exchange_counts:
                exchange_counts[match.exchange] = []
            exchange_counts[match.exchange].append(match.symbol)
        
        print('\n=== 各交易所匹配統計 ===')
        for exchange, symbols in exchange_counts.items():
            unique_symbols = list(set(symbols))
            print(f'{exchange}: {unique_symbols} ({len(symbols)} 個網路)')
                
    except Exception as e:
        import traceback
        print(f'[錯誤] {e}')
        print(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(test_babydoge_complete())