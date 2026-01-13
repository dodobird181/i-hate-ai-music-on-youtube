from logging import getLogger

from peewee import Model

from db import get_db

logger = getLogger(__name__)

db = get_db()


class BaseModel(Model):
    class Meta:
        database = db


from models.video import Video

if True:
    # Must be after Video, since Comment has a FK pointing to Video
    from models.comment import Comment

APP_MODELS = [Video, Comment]


try:
    # Initialize a database connection on module-load
    logger.info("Connecting to database...")
    db.connect()
    db.create_tables(APP_MODELS)
    logger.info("Successfully connected to the database: {}!".format(db.database))
except Exception as e:
    logger.error("Failed to connect to the database: {}!".format(db.database), exc_info=e)
