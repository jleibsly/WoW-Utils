#!/usr/bin/python3

import argparse
import db_helpers
import json

from db_helpers import DBKeys

"""
Still very hacky, I need to refactor it.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="WoW Market Data",
                                     description="Interface to query a local "
                                     + "database of WoW Classic market data."
                                     )
    parser.add_argument("item_name",
                        help="Name of the item to search for.")
    args = parser.parse_args()

    db = db_helpers.read_db()
    items_db = db[DBKeys.ITEMS.value]
    result = [k for (k, v) in items_db.items()
              if args.item_name.lower() in v['name'].lower()]

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

    print(json.dumps(items_db[result_item_id], sort_keys=True, indent=4, separators=(',', ': ')))
