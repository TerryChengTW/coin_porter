#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from typing import Dict, Set, List

def analyze_binance_identifiers(data: List[Dict]) -> Set[str]:
    """分析 Binance 的唯一識別符: network:name:contract_address_url"""
    identifiers = set()
    
    for coin_data in data:
        if 'network_list' in coin_data:
            for network in coin_data['network_list']:
                network_code = network.get('network', '')
                name = network.get('name', '')
                contract_url = network.get('contract_address_url', 'null')
                
                identifier = f"{network_code}:{name}:{contract_url}"
                identifiers.add(identifier)
    
    return identifiers

def analyze_bitget_identifiers(data: Dict) -> Set[str]:
    """分析 Bitget 的唯一識別符: chain:browserUrl"""
    identifiers = set()
    
    if 'data' in data:
        for coin_data in data['data']:
            if 'chains' in coin_data:
                for chain in coin_data['chains']:
                    chain_code = chain.get('chain', '')
                    browser_url = chain.get('browserUrl', 'null')
                    
                    identifier = f"{chain_code}:{browser_url}"
                    identifiers.add(identifier)
    
    return identifiers

def analyze_bybit_identifiers(data: Dict) -> Set[str]:
    """分析 Bybit 的唯一識別符: chain:chainType"""
    identifiers = set()
    
    if 'result' in data and 'rows' in data['result']:
        for coin_data in data['result']['rows']:
            if 'chains' in coin_data:
                for chain in coin_data['chains']:
                    chain_code = chain.get('chain', '')
                    chain_type = chain.get('chainType', '')
                    
                    identifier = f"{chain_code}:{chain_type}"
                    identifiers.add(identifier)
    
    return identifiers

def main():
    """主程序：分析三個交易所的網絡識別符"""
    
    # 檔案路徑
    base_path = r"C:\Users\terry\Desktop\dev\coin_porter\docs\api-response-examples"
    
    files = {
        'binance': os.path.join(base_path, 'binance', 'all_coins_information_full_response.json'),
        'bitget': os.path.join(base_path, 'bitget', 'public_coins_full_response.json'),
        'bybit': os.path.join(base_path, 'bybit', 'coin_info_full_response.json')
    }
    
    results = {
        'exchange_identifier_rules': {
            'binance': 'network:name:contract_address_url',
            'bitget': 'chain:browserUrl', 
            'bybit': 'chain:chainType'
        },
        'unique_combinations': {}
    }
    
    # 分析每個交易所
    for exchange, file_path in files.items():
        print(f"[INFO] 分析 {exchange.upper()}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if exchange == 'binance':
                identifiers = analyze_binance_identifiers(data)
            elif exchange == 'bitget':
                identifiers = analyze_bitget_identifiers(data)
            elif exchange == 'bybit':
                identifiers = analyze_bybit_identifiers(data)
            
            results['unique_combinations'][exchange] = {
                'count': len(identifiers),
                'identifiers': sorted(list(identifiers))
            }
            
            print(f"[OK] {exchange.upper()}: 找到 {len(identifiers)} 個不重複組合")
            
        except FileNotFoundError:
            print(f"[ERROR] 檔案不存在: {file_path}")
            results['unique_combinations'][exchange] = {
                'count': 0,
                'identifiers': [],
                'error': 'File not found'
            }
        except Exception as e:
            print(f"[ERROR] {exchange.upper()} 分析失敗: {str(e)}")
            results['unique_combinations'][exchange] = {
                'count': 0,
                'identifiers': [],
                'error': str(e)
            }
    
    # 輸出結果到 JSON
    output_file = r"C:\Users\terry\Desktop\dev\coin_porter\network_identifiers_analysis.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] 結果已儲存到: {output_file}")
    
    # 顯示摘要
    print("\n=== 摘要 ===")
    for exchange, data in results['unique_combinations'].items():
        if 'error' not in data:
            print(f"{exchange.upper()}: {data['count']} 個不重複組合")
        else:
            print(f"{exchange.upper()}: 錯誤 - {data['error']}")

if __name__ == "__main__":
    main()