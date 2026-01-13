import os
import sqlite3
import sys
from sqlite3 import Connection
from typing import List

import dotenv

# Resolve which database to connect to
dotenv.load_dotenv()
if "pytest" in sys.modules:
    DB_PATH = os.environ["TEST_DB_PATH"]
else:
    DB_PATH = os.environ["DB_PATH"]


def init_db():
    """
    Initialize the database.
    """
    with open("models/schema.sql") as file:
        schema = file.read()
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(schema)


# Initial initialization of the database (on module load)
init_db()


def db_conn() -> Connection:
    """
    Return a connection to the database.
    """
    connection = sqlite3.connect(DB_PATH)
    # returns database rows as dictionaries
    connection.row_factory = sqlite3.Row
    return connection


def fill_from(source: dict, template: dict) -> dict:
    """
    Traverse `template` and fill its values using matching keys from `source`.
    """
    result = {}

    for key, template_value in template.items():
        if isinstance(template_value, dict):
            # Recurse if both sides are dicts
            source_value = source.get(key, {})
            if isinstance(source_value, dict):
                result[key] = fill_from(source_value, template_value)
            else:
                result[key] = fill_from({}, template_value)
        else:
            # Leaf node
            result[key] = source.get(key, template.get(key, None))

    return result


def find_none_paths(obj: dict, _path: str = "") -> List[str]:
    """
    Find all paths leading to None. E.g. {"foo": {"bar": None}} -> ["foo.bar"]
    """

    paths: List[str] = []

    if obj is None:
        paths.append(_path)
        return paths

    if isinstance(obj, dict):
        for k, v in obj.items():
            paths.extend(find_none_paths(v, f"{_path}.{k}" if _path else k))

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            paths.extend(find_none_paths(v, f"{_path}[{i}]"))

    return paths


from models.channel import Channel
from models.comment import Comment
from models.video import Video
