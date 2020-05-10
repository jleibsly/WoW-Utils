#!/usr/bin/python3

import argparse
import db_helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="WoW Market Data",
                                     description="Interface to query a local "
                                     + "database of WoW Classic market data."
    )
    parser.add_argument("item_name", 
                        help="Name of the item to search for.")

    db = db_helpers.read_db()