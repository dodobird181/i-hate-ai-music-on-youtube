from logging import getLogger
from sys import modules

from peewee import Model, PostgresqlDatabase

from src.settings import (
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

"""
Database initialization code for Peewee models.
"""

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
    from src.models import APP_MODELS

    logger.debug("Resetting the test database...")
    db = _test_db()
    try:
        db.connect()
        db.drop_tables(APP_MODELS)
        db.create_tables(APP_MODELS)
        logger.info("Successfully connected to the database: {}!".format(db.database))
    except Exception as e:
        logger.error("Failed to connect to the database: {}!".format(db.database), exc_info=e)


db = get_db()


class BaseModel(Model):
    class Meta:
        database = db


from src.models.channel import Channel
from src.models.video import Video

if True:
    # Must be imported after Video, since Comment has a FK pointing to Video
    from src.models.comment import Comment

# For creating tables (and destroying them in tests)
APP_MODELS = [Video, Comment, Channel]


try:
    # Initialize a database connection on module-load
    logger.info("Connecting to database...")
    db.connect()
    db.create_tables(APP_MODELS)
    logger.info("Successfully connected to the database: {}!".format(db.database))
except Exception as e:
    logger.error("Failed to connect to the database: {}!".format(db.database), exc_info=e)
