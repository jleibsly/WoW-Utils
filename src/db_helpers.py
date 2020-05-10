#!/usr/bin/python3

import json
import os.path

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