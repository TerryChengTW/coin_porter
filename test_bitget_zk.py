#!/usr/bin/env python3
"""
測試 Bitget ZK 合約地址修正
"""

import sys
import os
import asyncio

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.exchanges.bitget import BitgetExchange
from src.core.exchanges.base import AccountConfig


async def test_zk_contract():
    """測試 ZK 合約地址顯示"""
    print("=== 測試 Bitget ZK 合約地址修正 ===")
    
    # 創建測試用的帳號配置
    test_config = AccountConfig(
        name='test_account',
        api_key='test_key',
        secret='test_secret', 
        passphrase='test_passphrase'
    )
    
    # 創建 Bitget 交易所實例
    exchange = BitgetExchange(test_config)
    
    try:
        # 查詢 ZK 幣種
        print("🔍 查詢 ZK 幣種網路資訊...")
        networks = await exchange.get_currency_networks('ZK')
        
        print(f"📊 找到 {len(networks)} 個網路")
        
        for i, network in enumerate(networks):
            print(f"\n  網路 {i+1}:")
            print(f"    網路名稱: {network.network}")
            print(f"    合約地址: {network.contract_address}")
            print(f"    完整網路名: {network.network_full_name}")
            print(f"    瀏覽器URL: {network.browser_url}")
            print(f"    最小出金: {network.min_withdrawal}")
            print(f"    手續費: {network.withdrawal_fee}")
            print(f"    入金狀態: {network.deposit_enabled}")
            print(f"    出金狀態: {network.withdrawal_enabled}")
        
        # 檢查是否包含預期的以太坊合約地址
        expected_contract = "0x5a7d6b2f92c77fad6ccabd7ee0624e64907eaf3e"
        found_expected = False
        
        for network in networks:
            if network.contract_address and network.contract_address.lower() == expected_contract.lower():
                print(f"\n✅ 找到預期的 ZK 合約地址！")
                print(f"   網路: {network.network}")
                print(f"   合約: {network.contract_address}")
                found_expected = True
                break
        
        if not found_expected:
            print(f"\n❌ 未找到預期的合約地址 {expected_contract}")
            print("📋 實際找到的合約地址:")
            for network in networks:
                if network.contract_address:
                    print(f"   {network.network}: {network.contract_address}")
        
        return networks
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """主函數"""
    print("開始測試 Bitget ZK 合約地址修正...\n")
    
    try:
        networks = asyncio.run(test_zk_contract())
        
        if networks:
            print(f"\n🎉 測試完成！找到 {len(networks)} 個網路")
            
            # 檢查修正是否生效
            has_contracts = any(net.contract_address for net in networks)
            if has_contracts:
                print("✅ 合約地址字段已正確填入")
            else:
                print("⚠️ 未發現合約地址，可能需要進一步檢查")
        else:
            print("❌ 未能獲取網路資訊")
            
    except Exception as e:
        print(f"❌ 主測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()