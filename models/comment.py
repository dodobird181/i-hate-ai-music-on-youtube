from peewee import CharField, DateTimeField, ForeignKeyField, TextField

from . import BaseModel, Video


class Comment(BaseModel):

    id = CharField(max_length=255, primary_key=True)
    text = TextField()
    video = ForeignKeyField(model=Video)
    published_at = DateTimeField()
    author_channel_id = CharField(max_length=255)
