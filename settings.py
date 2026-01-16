from logging import WARNING, basicConfig, getLevelNamesMapping, getLogger
from os import environ

from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = environ["LOG_LEVEL"]

basicConfig(level=getLevelNamesMapping()[LOG_LEVEL], format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
getLogger("peewee").setLevel(WARNING)
getLogger("googleapiclient").setLevel(WARNING)
getLogger("urllib3").setLevel(WARNING)
getLogger("matplotlib").setLevel(WARNING)
getLogger("PIL").setLevel(WARNING)

POSTGRES_DB = environ["POSTGRES_DB"]
POSTGRES_USER = environ["POSTGRES_USER"]
POSTGRES_PASSWORD = environ["POSTGRES_PASSWORD"]
POSTGRES_PORT = environ["POSTGRES_PORT"]
POSTGRES_HOST = environ["POSTGRES_HOST"]

TEST_POSTGRES_DB = environ["TEST_POSTGRES_DB"]
TEST_POSTGRES_USER = environ["TEST_POSTGRES_USER"]
TEST_POSTGRES_PASSWORD = environ["TEST_POSTGRES_PASSWORD"]
TEST_POSTGRES_PORT = environ["TEST_POSTGRES_PORT"]
TEST_POSTGRES_HOST = environ["TEST_POSTGRES_HOST"]
