#!/usr/bin/python3

import argparse
import db_helpers
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
    ITEM_DETAILS = f"item/"
    LAST_SCAN = f"scans/latest/{SERVER}/"


def _load_json(endpoint):
    """
    Load the endpoint, passing in the hacky SSL context. Then, parse
    it into a json object and return it.
    """

    # We are accepting either a string or instance of APIEndpoint.
    # If it's of type APIEndpoint, we need to call `.value` to convert
    # it to a string.
    val = endpoint if isinstance(endpoint, str) else endpoint.value
    return json.loads(
        urllib.request.urlopen(
            f"https://api.nexushub.co/wow-classic/v1/{val}",
            context=HACKY_SSL_CONTEXT
        ).read()
    )


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
        int(datetime.strptime(
            json['scannedAt'],
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ).timestamp())
    )


def _update_prices(db):
    """
    Function that will open the given DB, call the ALL_ITEMS
    endpoint, and update the DB for each item with its current
    information.
    """
    print("Updating market data with latest market scan...")

    prices_db = db[DBKeys.PRICES.value]
    items_json = _load_json(APIEndpoint.ALL_ITEMS)
    """
    Explanation of what's about to happen:
    Ok, so, we get it back from the server in the format of:
    {
        'slug': 'earthfury-horde',
        'data': [
            {
                'itemId': 8350,
                'marketValue': 307169,
                'previous': {
                    'marketValue': 297483,
                    'historicalValue': 257420,
                    'minBuyout': 390000,
                    'numAuctions': 1,
                    'quantity': 1
                },
                'historicalValue': 256000,
                'minBuyout': 0,
                'numAuctions': 0,
                'quantity': 0
            },
            {...} // Same as the above dictionary for another item
        ]
    }

    What we want is to convert this so we have a dictionary of all items
    where their itemId is the key and the rest of the info is the value.
    We also want to know when the item was scanned. So we want the
    dictionary to look like this:
    {
        8350: {
            TIMESTAMP_OF_SCAN: {
                'marketValue': 307169,
                'minBuyout': 0,
                'numAuctions': 0,
                'quantity': 0
            }
    }

    Note that I got rid of "previous" since we'll scrape our own history
    over time, and this field would become redundant. I also nixed
    'historicalValue' because I have no idea what it represents.
    """

    # Go through each item from the server, see the json above in the
    # explanation.
    scan_timestamp = db[DBKeys.LAST_UPDATED.value]
    for item_from_server in items_json['data']:
        # setdefault will get the item from the prices_db if it exists,
        # otherwise it will set it to `{}` and return that. We need to
        # convert the item id to a string because the json serializer
        # does not allow integer keys in dictionaries.
        item_in_db = prices_db.setdefault(str(item_from_server['itemId']), {})

        # I'm doing this instead of copying the dict from the server so we
        # can remove keys or update their names in our local db if we want.
        # We convert the timestamp to a string for the same reason we converted
        # the item id to a string above.
        item_in_db[str(scan_timestamp)] = {
            'marketValue': item_from_server['marketValue'],
            'minBuyout': item_from_server['minBuyout'],
            'numAuctions': item_from_server['numAuctions'],
            'quantity': item_from_server['quantity'],
        }
        break
    # Note: We do not need to return anything because we are directly
    # updating the db.


def _update_items(db):
    """
    Get item details for everything we have price info on.
    """
    items_db = db[DBKeys.ITEMS.value]

    # We keep track of the last time we called the API. This is because they limit us
    # to 4 requests per second.
    last_call_to_api_timestamp = 0

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

        # Time in milliseconds that elapsed since the last call.
        elapsed = (time.time() * 1000) - last_call_to_api_timestamp

        # If it's been under a quarter of a second, wait until a full quarter
        # second has passed.
        if elapsed < 250:
            time.sleep(250 - elapsed)

        # Load the item in to the db from the item details endpoint.
        items_db[item_id] = _load_json("{}{}".format(
            APIEndpoint.ITEM_DETAILS.value,
            item_id
        ))


if __name__ == "__main__":
    # Read in the local db.
    db = db_helpers.read_db()

    # We don't use the scan id that _fetch_last_scan_info returns, just the timestamp
    # of the latest scan.
    (_, scan_timestamp) = _fetch_last_scan_info()

    # Only update the db if the latest scan is later than the last time we
    # updated the db.
    if db[DBKeys.LAST_UPDATED.value] < scan_timestamp:
        db[DBKeys.LAST_UPDATED.value] = scan_timestamp
        _update_prices(db)
        _update_items(db)
    else:
        print("Nothing to update!")

    # Write the db back to the json file.
    db_helpers.write_db(db)
