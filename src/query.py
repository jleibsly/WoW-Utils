#!/usr/bin/python3

import argparse
import csv
import db_helpers
import json

from db_helpers import DBKeys

"""
Still very hacky, I need to refactor it.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="WoW Market Data Query Interface",
                                     description="Interface to query a local "
                                     + "database of WoW Classic market data."
                                     )
    parser.add_argument("item_name",
                        help="Name of the item to search for.")
    parser.add_argument("--outfile", "-o", required=False,
                        help="If provided, will output price history for the item to the file.")
    parser.add_argument("--output-type", "-t", default="csv", choices=["csv", "json"],
                        help="If provided, will output info for the item to the file.")
    args = parser.parse_args()

    db = db_helpers.read_db()
    items_db = db[DBKeys.ITEMS.value]
    for (k, v) in items_db.items():
        if 'name' not in v:
            print(v)
    result = [k for (k, v) in items_db.items()
              if 'name' in v and args.item_name.lower() in v['name'].lower()]

    if len(result) == 1:
        result_item_id = result[0]
    elif len(result) == 0:
        print("No results!")
        exit(0)
    else:
        i = 1
        for r in result:
            name = items_db[r]['name']
            print(f"{i}. {name}")
            i += 1
        user_input = int(input("Which item are you searching for (the #)?\n"))
        if user_input > 0 and user_input < i:
            result_item_id = result[user_input - 1]
        else:
            print("Invalid selection.")
            exit(0)

    print("Item Details\n================================")
    print(
        json.dumps(
            items_db[result_item_id],
            sort_keys=True,
            indent=4,
            separators=(
                ',',
                ': ')))
    print("\n\nPrice History\n================================")
    price_history_data = db[DBKeys.PRICES.value][result_item_id]

    formatted_output = []
    for (timestamp, data) in price_history_data.items():
        formatted_date = db_helpers.formatted_local_date_from_timestamp(timestamp)
        formatted_output.append({
            "Date": formatted_date.strftime("%Y/%m/%d, %H:%M:%S"),
            "Market Value": data['marketValue'],
            "Minimum Buyout": data['minBuyout'],
            "Number of Auctions": data.get('numAuctions', 'NA'),
            "Quantity": data['quantity']
        })
        print(formatted_date)
        print(
            "Market Value: {}\nMin Buyout: {}\nNumber of Auctions: {}\nQuantity: {}\n".format(
                db_helpers.formatted_price(
                    data['marketValue']), db_helpers.formatted_price(
                    data['minBuyout']), data['numAuctions'], data['quantity']))
    if args.outfile:
        formatted_output.sort(key=lambda k: k['Date'])
        if args.output_type == "json":
            json.dump(formatted_output, open(args.outfile, "w"))
        elif args.output_type == "csv":
            keys = formatted_output[0].keys()
            dict_writer = csv.DictWriter(open(args.outfile, "w"), keys)
            dict_writer.writeheader()
            dict_writer.writerows(formatted_output)
