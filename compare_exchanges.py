#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from typing import Dict, Set, List, Tuple

def normalize_network_name(name: str) -> str:
    """標準化網絡名稱用於比較"""
    # 移除常見的括號內容
    name = re.sub(r'\([^)]*\)', '', name).strip()
    # 統一大小寫
    name = name.upper()
    # 移除常見的後綴
    name = re.sub(r'\s+(CHAIN|NETWORK|MAINNET|PROTOCOL)$', '', name)
    return name

def extract_network_info(identifier: str, exchange: str) -> Tuple[str, str, str]:
    """從識別符中提取網絡資訊"""
    parts = identifier.split(':')
    
    if exchange == 'binance':
        # network:name:contract_address_url
        network = parts[0] if len(parts) > 0 else ''
        name = parts[1] if len(parts) > 1 else ''
        url = parts[2] if len(parts) > 2 else ''
        return network, name, url
    elif exchange == 'bitget':
        # chain:browserUrl
        network = parts[0] if len(parts) > 0 else ''
        name = network  # Bitget 沒有描述性名稱
        url = parts[1] if len(parts) > 1 else ''
        return network, name, url
    elif exchange == 'bybit':
        # chain:chainType
        network = parts[0] if len(parts) > 0 else ''
        name = parts[1] if len(parts) > 1 else ''
        url = ''  # Bybit 沒有瀏覽器URL
        return network, name, url
    
    return '', '', ''

def find_similar_networks():
    """比較三個交易所的相似網絡"""
    
    # 讀取分析結果
    with open(r"C:\Users\terry\Desktop\dev\coin_porter\network_identifiers_analysis.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 整理每個交易所的網絡資訊
    exchanges_networks = {}
    
    for exchange, info in data['unique_combinations'].items():
        networks = {}
        for identifier in info['identifiers']:
            network_code, name, url = extract_network_info(identifier, exchange)
            
            # 提取domain from URL
            domain = ''
            if url and url != 'None' and url != 'null':
                match = re.search(r'https?://([^/]+)', url)
                if match:
                    domain = match.group(1)
            
            networks[network_code] = {
                'name': name,
                'url': url,
                'domain': domain,
                'normalized_name': normalize_network_name(name)
            }
        
        exchanges_networks[exchange] = networks
    
    # 比較相似性
    comparison_results = {
        'network_name_mapping': {},
        'explorer_domains': {},
        'cross_exchange_analysis': []
    }
    
    # 分析網絡名稱對應
    all_networks = set()
    for exchange, networks in exchanges_networks.items():
        all_networks.update(networks.keys())
    
    for network in sorted(all_networks):
        mapping = {}
        for exchange in ['binance', 'bitget', 'bybit']:
            if network in exchanges_networks[exchange]:
                info = exchanges_networks[exchange][network]
                mapping[exchange] = {
                    'network_code': network,
                    'name': info['name'],
                    'domain': info['domain']
                }
        
        if len(mapping) > 1:  # 至少兩個交易所有相同網絡代碼
            comparison_results['network_name_mapping'][network] = mapping
    
    # 分析瀏覽器域名
    all_domains = {}
    for exchange, networks in exchanges_networks.items():
        for network_code, info in networks.items():
            if info['domain']:
                if info['domain'] not in all_domains:
                    all_domains[info['domain']] = {}
                if exchange not in all_domains[info['domain']]:
                    all_domains[info['domain']][exchange] = []
                all_domains[info['domain']][exchange].append(network_code)
    
    comparison_results['explorer_domains'] = all_domains
    
    # 跨交易所分析
    for network in sorted(comparison_results['network_name_mapping'].keys()):
        mapping = comparison_results['network_name_mapping'][network]
        analysis = {
            'network_code': network,
            'exchanges': list(mapping.keys()),
            'name_consistency': len(set([info['name'] for info in mapping.values()])) == 1,
            'domain_consistency': len(set([info['domain'] for info in mapping.values() if info['domain']])) <= 1,
            'details': mapping
        }
        comparison_results['cross_exchange_analysis'].append(analysis)
    
    # 輸出結果
    output_file = r"C:\Users\terry\Desktop\dev\coin_porter\exchange_comparison_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] 交易所比較結果已儲存到: {output_file}")
    
    # 顯示重要發現
    print("\n=== 重要發現 ===")
    
    # 相同網絡代碼但不同命名
    inconsistent_names = [item for item in comparison_results['cross_exchange_analysis'] 
                         if not item['name_consistency']]
    
    print(f"相同網絡代碼但名稱不一致: {len(inconsistent_names)} 個")
    for item in inconsistent_names[:10]:  # 顯示前10個
        print(f"  {item['network_code']}: {[info['name'] for info in item['details'].values()]}")
    
    # 共同的瀏覽器域名
    shared_domains = {domain: exchanges for domain, exchanges in all_domains.items() 
                     if len(exchanges) > 1}
    print(f"\n共用瀏覽器域名: {len(shared_domains)} 個")
    for domain, exchanges in list(shared_domains.items())[:10]:
        print(f"  {domain}: {list(exchanges.keys())}")

if __name__ == "__main__":
    find_similar_networks()