"""
測試新的統一 get_all_coins_info API
"""

import sys
import asyncio
from pathlib import Path

# 添加源碼路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.exchanges.manager import ExchangeManager
from src.core.config.api_keys import APIKeyManager


async def test_unified_api():
    """測試統一的 get_all_coins_info API"""
    print("=== 測試統一 get_all_coins_info API ===")
    
    try:
        # 初始化管理器
        api_manager = APIKeyManager()
        exchange_manager = ExchangeManager(api_manager)
        
        # 測試三個交易所
        exchanges_to_test = ["binance", "bybit", "bitget"]
        
        for exchange_name in exchanges_to_test:
            print(f"\n--- 測試 {exchange_name.upper()} ---")
            
            try:
                exchange = exchange_manager._exchanges.get(exchange_name)
                if not exchange:
                    print(f"❌ {exchange_name} 交易所實例不存在")
                    continue
                
                # 呼叫新的統一 API
                coins_info = await exchange.get_all_coins_info()
                
                print(f"✅ {exchange_name} 成功獲取 {len(coins_info)} 個幣種的完整資訊")
                
                # 顯示前幾個幣種的範例
                for i, coin in enumerate(coins_info[:3]):
                    print(f"  幣種 {i+1}: {coin.symbol}")
                    print(f"    完整名稱: {coin.full_name}")
                    print(f"    支援網路數量: {len(coin.networks)}")
                    print(f"    交易啟用: {coin.trading_enabled}")
                    print(f"    入金啟用: {coin.deposit_all_enabled}")
                    print(f"    出金啟用: {coin.withdrawal_all_enabled}")
                    
                    # 顯示第一個網路的詳細資訊
                    if coin.networks:
                        network = coin.networks[0]
                        print(f"    第一個網路: {network.network}")
                        print(f"      最小出金: {network.min_withdrawal}")
                        print(f"      手續費: {network.withdrawal_fee}")
                        print(f"      合約地址: {network.contract_address}")
                    print()
                
                # 測試特定幣種查找
                test_symbols = ["BTC", "ETH", "USDT", "BABYDOGE", "1MBABYDOGE"]
                found_symbols = []
                
                for coin in coins_info:
                    if coin.symbol in test_symbols:
                        found_symbols.append(coin.symbol)
                
                print(f"  在 {len(coins_info)} 個幣種中找到測試符號: {found_symbols}")
                
            except Exception as e:
                print(f"❌ {exchange_name} 測試失敗: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n🎉 統一API測試完成")
        
    except Exception as e:
        print(f"[錯誤] 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_unified_api())