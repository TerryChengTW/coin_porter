# API Response Examples

This directory contains pure API response examples from cryptocurrency exchanges for development reference.

## Directory Structure

```
docs/api-response-examples/
├── binance/
│   ├── all_coins_information.json    # GET /sapi/v1/capital/config/getall
│   ├── balance.json                  # GET /sapi/v1/account/balance (future)
│   └── deposit_address.json          # POST /sapi/v1/capital/deposit/address (future)
├── bybit/
│   ├── coin_info.json               # GET /v5/asset/coin/query-info
│   ├── balance.json                 # GET /v5/asset/transfer/query-account-coins-balance (future)
│   └── deposit_address.json         # GET /v5/asset/deposit/query-address (future)
├── bitget/
│   ├── public_coins.json            # GET /api/v2/spot/public/coins
│   ├── balance.json                 # GET /api/v2/spot/account/assets (future)
│   └── deposit_address.json         # GET /api/v2/spot/wallet/deposit-address (future)
└── README.md
```

## Response Format

- **Pure API responses** - No additional metadata wrapper
- **Original structure** - Exactly as returned by exchange APIs
- **UTF-8 encoded** - Supports international characters

## Usage

- **Development reference** - Understanding API response structures
- **Testing** - Mock data for unit tests
- **Documentation** - API behavior examples
- **Debugging** - Compare actual vs expected responses

## Notes

- Files contain real API responses (anonymized where needed)
- Response times and IDs may vary between calls
- Some responses may be truncated for readability