#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
幣安提幣功能測試腳本
測試幣安的提幣API端點：POST /sapi/v1/capital/withdraw/apply
"""

import json
import asyncio
from typing import Optional
from datetime import datetime

try:
    from binance_common.configuration import ConfigurationRestAPI
    from binance_common.constants import WALLET_REST_API_PROD_URL
    from binance_sdk_wallet.wallet import Wallet
    print("[成功] Binance SDK 導入成功")
except ImportError as e:
    print(f"[錯誤] Binance SDK 導入失敗: {e}")
    print("請確認已安裝 binance SDK")
    exit(1)


class BinanceWithdrawTester:
    """幣安提幣功能測試器"""
    
    def __init__(self, api_key: str, secret: str):
        self.api_key = api_key
        self.secret = secret
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """設定 Binance 客戶端"""
        try:
            configuration = ConfigurationRestAPI(
                api_key=self.api_key,
                api_secret=self.secret,
                base_path=WALLET_REST_API_PROD_URL
            )
            
            self.client = Wallet(config_rest_api=configuration)
            print("[成功] Binance 客戶端初始化完成")
            
        except Exception as e:
            print(f"[錯誤] Binance 客戶端初始化失敗: {e}")
            raise
    
    async def test_withdraw(
        self,
        coin: str,
        address: str,
        amount: float,
        network: Optional[str] = None,
        address_tag: Optional[str] = None,
        name: Optional[str] = None,
        wallet_type: int = 0,
        transaction_fee_flag: bool = False,
        withdraw_order_id: Optional[str] = None,
        timestamp: Optional[int] = None
    ):
        """
        測試提幣功能
        
        Args:
            coin: 幣種符號 (如 USDT)
            address: 提幣地址
            amount: 提幣數量
            network: 網路類型 (如 TRC20, ERC20, BSC)
            address_tag: 地址標籤 (某些幣種需要，如 XRP, EOS)
            name: 地址的備註
            wallet_type: 錢包類型 (0=現貨錢包, 1=資金錢包)
            transaction_fee_flag: 站內轉賬時免手續費標誌
            withdraw_order_id: 用戶自定義提幣ID
        """
        if not self.client:
            raise Exception("客戶端未初始化")
        
        # 構建提幣參數
        import time
        withdraw_params = {
            "coin": coin,
            "address": address,
            "amount": str(amount),
            "wallet_type": wallet_type,
            "transaction_fee_flag": transaction_fee_flag
        }
        
        # 添加可選參數
        if network:
            withdraw_params["network"] = network
        if address_tag:
            withdraw_params["addressTag"] = address_tag
        if name:
            withdraw_params["name"] = name
        if withdraw_order_id:
            withdraw_params["withdraw_order_id"] = withdraw_order_id
        
        print(f"[INFO] 準備執行提幣操作")
        print(f"[INFO] 提幣參數: {json.dumps(withdraw_params, indent=2, ensure_ascii=False)}")
        
        try:
            # 執行提幣請求
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._execute_withdraw(withdraw_params)
            )
            
            print(f"[成功] 提幣請求已提交")
            
            # 正確顯示響應內容
            if hasattr(response, 'data'):
                response_data = response.data()
                print(f"[成功] 響應數據: {response_data}")
                if hasattr(response_data, '__dict__'):
                    print(f"[成功] 響應詳情: {vars(response_data)}")
            else:
                print(f"[成功] 響應物件: {response}")
            
            return response
            
        except Exception as e:
            print(f"[錯誤] 提幣失敗: {str(e)}")
            raise
    
    def _execute_withdraw(self, params: dict):
        """執行提幣API調用"""
        try:
            # 使用正確的 withdraw 方法
            return self.client.rest_api.withdraw(**params)
                
        except Exception as e:
            print(f"[錯誤] API 調用失敗: {e}")
            raise
    
    async def get_withdraw_history(self, coin: Optional[str] = None, limit: int = 10):
        """查詢提幣歷史"""
        try:
            params = {"limit": limit}
            if coin:
                params["coin"] = coin
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.rest_api.withdraw_history(**params)
            )
            
            print(f"[成功] 提幣歷史查詢完成")
            return response
            
        except Exception as e:
            print(f"[錯誤] 查詢提幣歷史失敗: {e}")
            raise
    
    async def get_coin_info(self, coin: Optional[str] = None):
        """查詢幣種資訊（包含網路和手續費）"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.rest_api.all_coins_information()
            )
            
            data = response.data()
            
            if coin:
                # 過濾特定幣種
                coin_data = [c for c in data if getattr(c, 'coin', '') == coin.upper()]
                if coin_data:
                    coin_info = coin_data[0]
                    print(f"[INFO] {coin} 幣種資訊:")
                    print(f"  幣種名稱: {getattr(coin_info, 'name', '')}")
                    print(f"  是否可提幣: {getattr(coin_info, 'withdraw_all_enable', False)}")
                    
                    networks = getattr(coin_info, 'network_list', [])
                    if networks:
                        print(f"  支援網路:")
                        for net in networks:
                            network_name = getattr(net, 'network', '')
                            withdraw_fee = getattr(net, 'withdraw_fee', '')
                            withdraw_min = getattr(net, 'withdraw_min', '')
                            withdraw_max = getattr(net, 'withdraw_max', '')
                            withdraw_enable = getattr(net, 'withdraw_enable', False)
                            
                            print(f"    - {network_name}: 可提幣={withdraw_enable}, 手續費={withdraw_fee}, 最小={withdraw_min}, 最大={withdraw_max}")
                    
                    return coin_info
                else:
                    print(f"[WARNING] 未找到 {coin} 幣種資訊")
                    return None
            else:
                print(f"[INFO] 總共查詢到 {len(data)} 個幣種")
                return data
            
        except Exception as e:
            print(f"[錯誤] 查詢幣種資訊失敗: {e}")
            raise


async def main():
    """主測試函數"""
    print("=== 幣安提幣功能測試 ===")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 讀取 API 配置
    try:
        with open("api_keys.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        binance_config = config.get("binance", {}).get("main", {})
        api_key = binance_config.get("api_key")
        secret = binance_config.get("secret")
        
        if not api_key or not secret:
            print("[錯誤] 未找到有效的幣安 API 配置")
            return
        
        print("[成功] API 配置讀取完成")
        
    except Exception as e:
        print(f"[錯誤] 讀取 API 配置失敗: {e}")
        return
    
    # 初始化測試器
    try:
        tester = BinanceWithdrawTester(api_key, secret)
    except Exception as e:
        print(f"[錯誤] 初始化測試器失敗: {e}")
        return
    
    try:
        # 1. 查詢 USDT 幣種資訊
        print("\n1. 查詢 USDT 幣種資訊...")
        await tester.get_coin_info("USDT")
        
        # 2. 查詢提幣歷史
        print("\n2. 查詢最近提幣歷史...")
        await tester.get_withdraw_history(limit=5)
        
        # 3. 測試提幣 (注意：這是真實交易，請謹慎使用！)
        print("\n3. 提幣測試 (僅顯示參數，不實際執行)")
        
        # USDT 透過 POLYGON 網路提幣到 Bybit
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_params = {
            "coin": "USDT",
            "address": "0xabcd", # 提幣對象地址
            "amount": 0.013,  # 測試金額 (POLYGON 最小 0.013)
            "network": "MATIC",  # USDT POLYGON 網路
            "withdraw_order_id": f"coin_porter_test_{timestamp_str}"
        }
        
        print(f"測試參數: {json.dumps(test_params, indent=2, ensure_ascii=False)}")
        print("[WARNING] 這是真實的提幣操作，請確認參數正確後再執行！")
        
        # 取消註釋以下行來實際執行提幣（請謹慎！）
        #result = await tester.test_withdraw(**test_params)
        
        # 正確顯示提幣結果
        print(f"[INFO] 提幣操作完成")
        if hasattr(result, 'data'):
            result_data = result.data()
            print(f"[結果] 提幣數據: {result_data}")
            if hasattr(result_data, '__dict__'):
                print(f"[結果] 提幣詳情: {json.dumps(vars(result_data), indent=2, ensure_ascii=False)}")
        else:
            print(f"[結果] 提幣響應: {result}")
        
    except Exception as e:
        print(f"[錯誤] 測試過程中發生錯誤: {e}")


if __name__ == "__main__":
    asyncio.run(main())