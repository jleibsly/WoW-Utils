#!/usr/bin/python3

import json
import os.path

from datetime import datetime, timezone
from enum import Enum


class DBKeys(Enum):
    LAST_UPDATED = "last_updated"
    PRICES = "prices"
    ITEMS = "items"


DEFAULT_DB_STRUCTURE = {
    DBKeys.LAST_UPDATED.value: 0,
    DBKeys.PRICES.value: {},
    DBKeys.ITEMS.value: {}
}


def db_path():
    """
    Get the relative path from to this script to the db.json file.
    """
    return os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "../data/db.json"
    )


def read_db():
    """
    Read in the local db file to a json object.
    """

    # If the file doesn't exist, create it.
    path = db_path()
    if not os.path.exists(path):
        return DEFAULT_DB_STRUCTURE

    # TODO: Handle corrupted file that doesn't read in or parse to json.
    with open(db_path(), "r") as f:
        db = json.load(f)
        f.close()
    return db


def write_db(db):
    """
    Write the db json object to the local db file.
    """
    with open(db_path(), "w") as f:
        json.dump(db, f, sort_keys=True, indent=4, separators=(',', ': '))
        f.close()


def formatted_local_date_from_timestamp(timestamp):
    return datetime.fromtimestamp(
        int(timestamp)).replace(
        tzinfo=timezone.utc).astimezone(
            tz=None)


def formatted_price(price):
    copper = int(price % 100)
    temp = (price - copper) / 100
    silver = int(temp % 100)
    gold = int((temp - silver) / 100)
    return f"{gold}g {silver}s {copper}c"
