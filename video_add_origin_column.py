from peewee import CharField
from playhouse.migrate import PostgresqlMigrator, migrate

from db import get_db

db = get_db()
migrator = PostgresqlMigrator(db)
migrate(migrator.add_column("video", "origin", CharField(max_length=255, default="scraped")))
