#!/usr/bin/python3

import argparse
import db_helpers

from db_helpers import DBKeys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="WoW Market Data",
                                     description="Interface to query a local "
                                     + "database of WoW Classic market data."
                                     )
    parser.add_argument("item_name",
                        help="Name of the item to search for.")
    args = parser.parse_args()

    db = db_helpers.read_db()
    result = [k for (k, v) in db[DBKeys.ITEMS.value].items()
              if args.item_name.lower() in v['name'].lower()]

    result_names = [db[DBKeys.ITEMS.value][k]['name'] for k in result]
    if len(result_names) == 1:
        name = result_names[0]
    elif len(result_names) == 0:
        print("No results!")
        exit(0)
    else:
        i = 1
        for n in result_names:
            print(f"{i}. {n}")
            i += 1
        user_input = int(input("Which item are you searching for (the #)?\n"))
        if user_input > 0 and user_input < i:
            name = result_names[user_input - 1]
        else:
            print("Invalid selection.")
            exit(0)

    print(name)
