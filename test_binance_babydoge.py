#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
sys.path.append('src')

from core.exchanges.binance import BinanceExchange
from core.config.api_keys import APIKeyManager

async def test_binance_babydoge():
    """直接測試 Binance BABYDOGE 查詢"""
    api_manager = APIKeyManager()
    
    # 獲取 Binance 帳號配置
    accounts = api_manager.get_exchange_accounts('binance')
    if not accounts:
        print('[錯誤] 沒有配置 Binance 帳號')
        return
    
    account_config = api_manager.get_account('binance', accounts[0])
    if not account_config:
        print('[錯誤] 無法獲取 Binance 帳號配置')
        return
    
    # 創建 Binance 交易所實例
    binance = BinanceExchange(account_config)
    
    try:
        print('[測試] 直接查詢 Binance BABYDOGE 網路...')
        networks = await binance.get_currency_networks('BABYDOGE')
        
        if networks:
            print(f'[成功] 找到 {len(networks)} 個 BABYDOGE 網路:')
            for net in networks:
                print(f'  - {net.network}: 提現費用 {net.withdrawal_fee}, 最小提現 {net.min_withdrawal}')
                print(f'    合約地址: {net.contract_address}')
        else:
            print('[問題] 沒有找到 BABYDOGE 網路')
            
        print('\n[測試] 查詢 1MBABYDOGE 網路（作為對照）...')
        networks_1m = await binance.get_currency_networks('1MBABYDOGE')
        
        if networks_1m:
            print(f'[對照] 找到 {len(networks_1m)} 個 1MBABYDOGE 網路:')
            for net in networks_1m:
                print(f'  - {net.network}: 提現費用 {net.withdrawal_fee}, 最小提現 {net.min_withdrawal}')
                print(f'    合約地址: {net.contract_address}')
        else:
            print('[對照] 沒有找到 1MBABYDOGE 網路')
            
    except Exception as e:
        import traceback
        print(f'[錯誤] {e}')
        print(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(test_binance_babydoge())