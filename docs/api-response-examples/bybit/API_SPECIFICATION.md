# Bybit 資產查詢幣種信息 API

## 接口描述
查詢幣種信息，獲取幣種信息，包括鏈信息，是否可充可提

## HTTP請求
```
GET /v5/asset/coin/query-info
```

## 請求參數
| 參數 | 是否必需 | 類型 | 說明 |
|------|----------|------|------|
| coin | false | string | 幣種 |

## 響應參數

### 根層級參數
| 參數 | 類型 | 說明 |
|------|------|------|
| retCode | Integer | 返回碼 |
| retMsg | String | 返回訊息 |
| result | Object | 結果對象 |
| retExtInfo | Object | 擴展信息 |
| time | Long | 時間戳 |

### 結果層級參數 (result)
| 參數 | 類型 | 說明 |
|------|------|------|
| rows | Array | 幣種信息數組 |

### 幣種層級參數 (rows)
| 參數 | 類型 | 說明 |
|------|------|------|
| name | String | 幣種名稱 |
| coin | String | 幣種符號 |
| **remainAmount** | String | **單筆提現最大數量** |
| chains | Array | 鏈信息數組 |

### 鏈層級參數 (chains)
| 參數 | 類型 | 說明 |
|------|------|------|
| chain | String | 鏈名 |
| **chainType** | String | **鏈類型 (詳細名稱)** |
| confirmation | String | 充值上賬確認數, 當到達該高度, 資金可用於交易 |
| withdrawFee | String | 提現手續費. **如果提現費為空，則表示該幣不支持提現** |
| depositMin | String | 最小充值數量 |
| withdrawMin | String | 最小提現數量 |
| **minAccuracy** | String | **充提幣的最小精度** |
| chainDeposit | String | 幣鏈是否可充值. 0: 暫停. 1: 正常 |
| chainWithdraw | String | 幣鏈是否可提幣. 0: 暫停. 1: 正常 |
| **withdrawPercentageFee** | String | **提現手續費百分比. 該字段的值是實際數字，即0.022表示為2.2%** |
| contractAddress | String | 合約地址. "" 表示沒有合約地址 |
| **safeConfirmNumber** | String | **風險高度數, 當入金抵達這個高度後, 風險完全解鎖, USD等值的資金允許提走** |

## 響應示例
```json
{
    "retCode": 0,
    "retMsg": "success",
    "result": {
        "rows": [
            {
                "name": "MNT",
                "coin": "MNT",
                "remainAmount": "10000000",
                "chains": [
                    {
                        "chainType": "Ethereum",
                        "confirmation": "6",
                        "withdrawFee": "3",
                        "depositMin": "0",
                        "withdrawMin": "3",
                        "chain": "ETH",
                        "chainDeposit": "1",
                        "chainWithdraw": "1",
                        "minAccuracy": "8",
                        "withdrawPercentageFee": "0",
                        "contractAddress": "0x3c3a81e81dc49a522a592e7622a7e711c06bf354",
                        "safeConfirmNumber": "65"
                    },
                    {
                        "chainType": "Mantle Network",
                        "confirmation": "100",
                        "withdrawFee": "0",
                        "depositMin": "0",
                        "withdrawMin": "10",
                        "chain": "MANTLE",
                        "chainDeposit": "1",
                        "chainWithdraw": "1",
                        "minAccuracy": "8",
                        "withdrawPercentageFee": "0",
                        "contractAddress": "",
                        "safeConfirmNumber": "100"
                    }
                ]
            }
        ]
    },
    "retExtInfo": {},
    "time": 1736395486989
}
```

## 重要特性
1. **name** - 幣種名稱
2. **coin** - 幣種符號
3. **chain** - 鏈名
4. **chainType** - 鏈類型 (詳細名稱)
5. **withdrawFee** - 提現手續費
6. **depositMin** - 最小充值數量
7. **withdrawMin** - 最小提現數量
8. **chainDeposit** - 幣鏈是否可充值 (0: 暫停. 1: 正常)
9. **chainWithdraw** - 幣鏈是否可提幣 (0: 暫停. 1: 正常)
10. **withdrawPercentageFee** - 提現手續費百分比
11. **contractAddress** - 合約地址