from logging import getLogger
from sys import modules

from peewee import PostgresqlDatabase

from settings import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    TEST_POSTGRES_DB,
    TEST_POSTGRES_HOST,
    TEST_POSTGRES_PASSWORD,
    TEST_POSTGRES_PORT,
    TEST_POSTGRES_USER,
)

logger = getLogger(__name__)


def _test_db() -> PostgresqlDatabase:
    return PostgresqlDatabase(
        database=TEST_POSTGRES_DB,
        user=TEST_POSTGRES_USER,
        password=TEST_POSTGRES_PASSWORD,
        host=TEST_POSTGRES_HOST,
        port=TEST_POSTGRES_PORT,
    )


def _db() -> PostgresqlDatabase:
    return PostgresqlDatabase(
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
    )


def get_db() -> PostgresqlDatabase:
    return _test_db() if "pytest" in modules else _db()


def reset_test_database() -> None:
    from models import APP_MODELS

    logger.debug("Resetting the test database...")
    db = _test_db()
    try:
        db.connect()
        db.drop_tables(APP_MODELS)
        db.create_tables(APP_MODELS)
        logger.info("Successfully connected to the database: {}!".format(db.database))
    except Exception as e:
        logger.error("Failed to connect to the database: {}!".format(db.database), exc_info=e)
