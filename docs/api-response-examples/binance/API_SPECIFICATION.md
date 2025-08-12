# Binance 獲取所有幣信息 API

## 接口描述
獲取針對用戶的所有(Binance支持充提操作的)幣種信息。

## HTTP請求
```
GET /sapi/v1/capital/config/getall
```

## 請求權重(IP)
10

## 請求參數
| 名稱 | 類型 | 是否必需 | 描述 |
|------|------|----------|------|
| recvWindow | LONG | NO | |
| timestamp | LONG | YES | |

## 響應參數

### 幣種層級參數
| 參數 | 類型 | 說明 |
|------|------|------|
| coin | String | 幣種符號 |
| depositAllEnable | Boolean | 是否支援所有網路充值 |
| withdrawAllEnable | Boolean | 是否支援所有網路提現 |
| name | String | 幣種完整名稱 |
| free | String | 可用餘額 |
| locked | String | 鎖定餘額 |
| freeze | String | 凍結餘額 |
| withdrawing | String | 提現中餘額 |
| ipoing | String | IPO中餘額 |
| ipoable | String | 可IPO餘額 |
| storage | String | 存儲餘額 |
| isLegalMoney | Boolean | 是否為法幣 |
| trading | Boolean | 是否支援交易 |
| networkList | Array | 支援的網路列表 |

### 網路層級參數 (networkList)
| 參數 | 類型 | 說明 |
|------|------|------|
| network | String | 網路名稱 |
| coin | String | 幣種符號 |
| **withdrawIntegerMultiple** | String | 提現整數倍數 |
| **isDefault** | Boolean | **是否為預設網路** |
| depositEnable | Boolean | 是否支援充值 |
| withdrawEnable | Boolean | 是否支援提現 |
| depositDesc | String | 充值描述 (僅在充值關閉時返回) |
| withdrawDesc | String | 提現描述 (僅在提現關閉時返回) |
| specialTips | String | 特殊提示 |
| specialWithdrawTips | String | 特殊提現提示 |
| name | String | 網路完整名稱 |
| resetAddressStatus | Boolean | 重置地址狀態 |
| **addressRegex** | String | **地址正則表達式** |
| **memoRegex** | String | **memo正則表達式** |
| withdrawFee | String | 提現手續費 |
| withdrawMin | String | 最小提現數量 |
| withdrawMax | String | 最大提現數量 |
| **withdrawInternalMin** | String | **內部轉帳最小提現數** |
| **depositDust** | String | **充值粉塵量** |
| **minConfirm** | Integer | **上帳所需的最小確認數** |
| **unLockConfirm** | Integer | **解鎖需要的確認數** |
| **sameAddress** | Boolean | **提現時是否需要memo** |
| **estimatedArrivalTime** | Integer | **預估到帳時間(小時)** |
| **busy** | Boolean | **網路是否繁忙** |
| contractAddressUrl | String | 合約地址瀏覽器URL |
| contractAddress | String | 合約地址 |
| **denomination** | Integer | **🔥 重要：換算比例 (1 1MBABYDOGE = 1000000 BABYDOGE)** |

## 響應示例
```json
[
    {
        "coin": "1MBABYDOGE",
        "depositAllEnable": true,
        "withdrawAllEnable": true,
        "name": "1M x BABYDOGE",
        "free": "34941.1",
        "locked": "0",
        "freeze": "0",
        "withdrawing": "0",
        "ipoing": "0",
        "ipoable": "0",
        "storage": "0",
        "isLegalMoney": false,
        "trading": true,
        "networkList": [
            {
                "network": "BSC",
                "coin": "1MBABYDOGE",
                "withdrawIntegerMultiple": "0.01",
                "isDefault": false,
                "depositEnable": true,
                "withdrawEnable": true,
                "depositDesc": "",
                "withdrawDesc": "",
                "specialTips": "",
                "specialWithdrawTips": "",
                "name": "BNB Smart Chain (BEP20)",
                "resetAddressStatus": false,
                "addressRegex": "^(0x)[0-9A-Fa-f]{40}$",
                "memoRegex": "",
                "withdrawFee": "10",
                "withdrawMin": "20",
                "withdrawMax": "9999999999",
                "withdrawInternalMin": "0.01",
                "depositDust": "0.01",
                "minConfirm": 5,
                "unLockConfirm": 0,
                "sameAddress": false,
                "estimatedArrivalTime": 1,
                "busy": false,
                "contractAddressUrl": "https://bscscan.com/token/",
                "contractAddress": "0xc748673057861a797275cd8a068abb95a902e8de",
                "denomination": 1000000
            }
        ]
    }
]
```

## 重要特性
1. **coin** - 幣種符號
2. **name** - 幣種完整名稱
3. **network** - 網路名稱
4. **coin** (networkList) - 幣種符號
5. **depositEnable** - 是否支援充值
6. **withdrawEnable** - 是否支援提現
7. **depositDesc** - 充值描述 (僅在充值關閉時返回)
8. **withdrawDesc** - 提現描述 (僅在提現關閉時返回)
9. **name** (networkList) - 網路完整名稱
10. **withdrawFee** - 提現手續費
11. **withdrawMin** - 最小提現數量
12. **withdrawMax** - 最大提現數量
13. **estimatedArrivalTime** - 預估到帳時間(小時)
14. **contractAddress** - 合約地址
15. **contractAddressUrl** - 合約地址瀏覽器URL
16. **busy** - 網路是否繁忙