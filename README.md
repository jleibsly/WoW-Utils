# WoW-Utils
## Usage
Running this will update `data/db.json` with the latest prices for each item as well as the details for each item. Subsequent calls will only update if newer scans are available from the server.
```
./src/scraper.py
```

## Querying Data
```
./src/query.py [item_name]
```
### Example
```
> ./src/query.py "Bolt of Linen Cloth"
Item Details
================================
{
    "icon": "https://wow.zamimg.com/images/wow/icons/large/inv_fabric_linen_02.jpg",
    "itemId": 2996,
    "itemLevel": 10,
    "itemLink": "|cffffffff|Hitem:2996::::::::::0|h[Bolt of Linen Cloth]|h|r",
    "name": "Bolt of Linen Cloth",
    "requiredLevel": 0,
    "sellPrice": 40,
    "tags": [
        "Common",
        "Trade Goods"
    ],
    "tooltip": [
        {
            "format": "Common",
            "label": "Bolt of Linen Cloth"
        },
        {
            "format": "Misc",
            "label": "Item Level 10"
        },
        {
            "label": "Max Stack: 10"
        },
        {
            "label": "Sell Price:"
        }
    ],
    "uniqueName": "bolt-of-linen-cloth",
    "vendorPrice": null
}


Price History
================================
2020-05-09 20:08:07-04:00
Market Value: 0g 1s 59c
Min Buyout: 0g 1s 0c
Number of Auctions: 17
Quantity: 150

2020-05-10 09:19:51-04:00
Market Value: 0g 1s 66c
Min Buyout: 0g 1s 4c
Number of Auctions: 14
Quantity: 93
```