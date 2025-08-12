# Bitget 行情獲取幣種信息 API

## 接口描述
獲取平台幣種信息，支持單個或全量查詢。該接口可獲取到的幣種與現貨賬戶支持的幣種一致

## HTTP請求
```
GET /api/v2/spot/public/coins
```

## 限速規則
3次/1s (IP)

## 請求參數
| 參數名 | 參數類型 | 必須 | 描述 |
|--------|----------|------|------|
| coin | String | 否 | 幣種名稱，如"BTC"。如不填寫，默認返回全部幣種信息 |

## 響應參數

### 根層級參數
| 參數 | 類型 | 說明 |
|------|------|------|
| code | String | 響應碼 |
| msg | String | 響應訊息 |
| requestTime | Long | 請求時間戳 |
| data | Array | 幣種數據數組 |

### 幣種層級參數 (data)
| 參數 | 類型 | 說明 |
|------|------|------|
| **coinId** | String | **幣種ID** |
| coin | String | 幣種名稱 |
| **transfer** | String | **是否可以劃轉** |
| chains | Array | 支持的鏈列表 |

### 鏈層級參數 (chains)
| 參數 | 類型 | 說明 |
|------|------|------|
| chain | String | 鏈名稱 |
| **needTag** | String | **是否需要tag** |
| withdrawable | String | 是否可提現 |
| rechargeable | String | 是否可充值 |
| withdrawFee | String | 提現手續費 |
| **extraWithdrawFee** | String | **額外收取, 鏈上轉賬銷毀，0.1表示10%** |
| depositConfirm | String | 充值確認塊數 |
| withdrawConfirm | String | 提現確認塊數 |
| minDepositAmount | String | 最小充值數 |
| minWithdrawAmount | String | 最小提現數 |
| browserUrl | String | 區塊瀏覽器地址 |
| contractAddress | String | 幣種合約地址 |
| **withdrawStep** | String | **提幣步長。非0，代表提幣數量需滿足步長倍數；為0，代表沒有步長倍數的限制** |
| **withdrawMinScale** | String | **提幣數量精度** |
| **congestion** | String | **鏈網路擁堵情況：normal(正常) / congested(擁堵)** |

## 響應示例
```json
{
    "code": "00000",
    "msg": "success",
    "requestTime": 1695799900330,
    "data": [
        {
            "coinId": "1",
            "coin": "BTC",
            "transfer": "true",
            "chains": [
                {
                    "chain": "BTC",
                    "needTag": "false",
                    "withdrawable": "true",
                    "rechargeable": "true",
                    "withdrawFee": "0.005",
                    "extraWithdrawFee": "0",
                    "depositConfirm": "1",
                    "withdrawConfirm": "1",
                    "minDepositAmount": "0.001",
                    "minWithdrawAmount": "0.001",
                    "browserUrl": "https://blockchair.com/bitcoin/testnet/transaction/",
                    "contractAddress": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "withdrawStep": "0",
                    "withdrawMinScale": "8",
                    "congestion": "normal"
                }
            ]
        }
    ]
}
```

## 重要特性
1. **coin** - 幣種名稱
2. **chains** - 支持的鏈列表
3. **chain** - 鏈名稱
4. **withdrawable** - 是否可提現
5. **rechargeable** - 是否可充值
6. **withdrawFee** - 提現手續費
7. **extraWithdrawFee** - 額外收取手續費百分比
8. **minDepositAmount** - 最小充值數
9. **minWithdrawAmount** - 最小提現數
10. **browserUrl** - 區塊瀏覽器地址
11. **contractAddress** - 幣種合約地址
12. **congestion** - 鏈網路擁堵情況