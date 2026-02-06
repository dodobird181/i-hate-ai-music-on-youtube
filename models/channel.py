from peewee import CharField, DateTimeField, TextField

from . import BaseModel


class Channel(BaseModel):
    id = CharField(primary_key=True, max_length=255)
    name = CharField(max_length=1024)
    description = TextField()
    created_at = DateTimeField()
