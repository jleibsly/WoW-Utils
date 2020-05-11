#!/usr/bin/python3

import argparse
import db_helpers
import functools
import json
import ssl
import time
import urllib.request

from datetime import datetime
from db_helpers import DBKeys
from enum import Enum

# Running without passing this results in an unverified SSL error. OH WELL.
HACKY_SSL_CONTEXT = ssl._create_unverified_context()

# We pass this in to the endpoints.
SERVER = "earthfury-horde"

# I like to put the endpoints in an enum so we can reference them in code without
# strings, like `APIEndpoint.ALL_ITEMS`.


class APIEndpoint(Enum):
    ALL_ITEMS = f"items/{SERVER}/"
    ITEM_DETAILS = "item/{}"
    ITEM_PRICE_HISTORY = ALL_ITEMS + "{}/prices"
    LAST_SCAN = f"scans/latest/{SERVER}/"


# Used for rate limiting, their docs say 20 calls per 5 seconds, 
# so 4 per second (or a quarter second between calls). 
# We rate limit the whole _load_json function; technically we
# should be rate limiting per endpoint, but this is simpler.
LAST_CALL_TO_API_TIMESTAMP = 0.0
MIN_TIME_BETWEEN_CALLS = 0.0
def _load_json(endpoint):
    """
    Load the endpoint, passing in the hacky SSL context. Then, parse
    it into a json object and return it.
    """
    
    # Tell the script we will be using and updating a global variable.
    global LAST_CALL_TO_API_TIMESTAMP
    # Calculate seconds since last API call.
    elapsed = time.time() - LAST_CALL_TO_API_TIMESTAMP
    if elapsed < MIN_TIME_BETWEEN_CALLS:
        time.sleep(MIN_TIME_BETWEEN_CALLS - elapsed)
    # We are accepting either a string or instance of APIEndpoint.
    # If it's of type APIEndpoint, we need to call `.value` to convert
    # it to a string.
    val = endpoint if isinstance(endpoint, str) else endpoint.value
    result = json.loads(
        urllib.request.urlopen(
            f"https://api.nexushub.co/wow-classic/v1/{val}",
            context=HACKY_SSL_CONTEXT
        ).read()
    )

    # Set the last call timestamp to after we call it.
    LAST_CALL_TO_API_TIMESTAMP = time.time()

    return result


def _fetch_last_scan_info():
    """
    Returns a tuple with the scan id as an integer, and scan date
    as a timestamp in seconds.

    NOTE: For the time format, I manually looked at what the endpoint
    returned, and formatted according to: https://bit.ly/2WGKv3l
    """
    json = _load_json(APIEndpoint.LAST_SCAN)
    return (
        json['scanId'],
        db_helpers.convert_server_timestamp_to_unix(json['scannedAt'])
    )


def _update_prices(db, exhaustive):
    """
    Function that will open the given DB, call the ALL_ITEMS
    endpoint, and update the DB for each item with its current
    information.
    """
    print("Updating market data with latest market scan...")

    prices_db = db[DBKeys.PRICES.value]

    def _update_item_in_db(item_json, item_id, timestamp):
        # setdefault will get the item from the prices_db if it exists,
        # otherwise it will set it to `{}` and return that. We need to
        # convert the item id to a string because the json serializer
        # does not allow integer keys in dictionaries.
        item_in_db = prices_db.setdefault(str(item_id), {})

        # I'm doing this instead of copying the dict from the server so we
        # can remove keys or update their names in our local db if we want.
        # We convert the timestamp to a string for the same reason we converted
        # the item id to a string above.
        ts_str = str(timestamp)
        if ts_str in item_in_db:
            return
        item_in_db[ts_str] = {
            'marketValue': item_json['marketValue'],
            'minBuyout': item_json['minBuyout'],
            # exhaustive updates do not have numAuctions
            'numAuctions': item_json.get('numAuctions', None),
            'quantity': item_json.get('quantity', None),
        }

    items_json = _load_json(APIEndpoint.ALL_ITEMS)
    timestamp = db[DBKeys.LAST_UPDATED.value]
    [_update_item_in_db(item, item['itemId'], timestamp) for item in items_json['data']]

    # We still update with all items and the latest scan above so that
    # we make sure we have all items in the db, even if they weren't in
    # a previous scan.
    if exhaustive:
        item_ids_to_update = prices_db.keys()
        total = len(item_ids_to_update)
        if total > 0:
            print(f"Fetching price history for {total} items...")
        i = 1
        for item_id in item_ids_to_update:
            print(f"{i}/{total}")
            i += 1
            # Fetch price history for the item.
            price_history = _load_json(
                APIEndpoint.ITEM_PRICE_HISTORY.value.format(item_id))['data']
            # Update price history for the item in the db.
            [
                _update_item_in_db(
                    d,
                    item_id,
                    db_helpers.convert_server_timestamp_to_unix(d['scannedAt'])
                )
                for d in price_history
            ]
    # Note: We do not need to return anything because we are directly
    # updating the db.


def _update_items(db):
    """
    Get item details for everything we have price info on.
    """
    items_db = db[DBKeys.ITEMS.value]

    # We only want to update items we don't already have information on.
    items_not_in_db = [i for i in db['prices'].keys() if i not in items_db]

    # Total number of items we need to fetch information for.
    total = len(items_not_in_db)
    if total > 0:
        print(f"Fetching details for {total} new items...")
    i = 1
    for item_id in items_not_in_db:
        # Print out what number we are on
        print(f"{i}/{total}")
        i += 1

        # Load the item in to the db from the item details endpoint.
        items_db[item_id] = _load_json(APIEndpoint.ITEM_DETAILS.value.format(
            item_id
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="WoW Market Data Scraper",
                                     description="Interface to update a local "
                                     + "database of WoW Classic market data."
                                     )
    parser.add_argument(
        "--exhaustive",
        "-e",
        action="store_true",
        help="Update the db by each individual item. Much slower, " +
        "but will update with all scans that were taken in the " +
        "last 24 hours.")
    args = parser.parse_args()

    # Read in the local db.
    db = db_helpers.read_db()

    # We don't use the scan id that _fetch_last_scan_info returns, just the timestamp
    # of the latest scan.
    (_, scan_timestamp) = _fetch_last_scan_info()

    # Only update the db if the latest scan is later than the last time we
    # updated the db. If 'exhaustive' is passed in, ignore timestamp comparison
    # and update everything.
    if db[DBKeys.LAST_UPDATED.value] < scan_timestamp or args.exhaustive:
        db[DBKeys.LAST_UPDATED.value] = scan_timestamp
        _update_prices(db, args.exhaustive)
        _update_items(db)
        print("All done!")
    else:
        print("Nothing to update!")

    # Write the db back to the json file.
    db_helpers.write_db(db)
