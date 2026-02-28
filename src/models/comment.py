from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from . import BaseModel, Video


class Comment(BaseModel):
    id = CharField(max_length=255, primary_key=True)
    text = TextField()
    video = ForeignKeyField(model=Video)
    author_channel_id = CharField(max_length=255)
    author_display_name = CharField(max_length=255)
    likes = IntegerField()
    is_reply = BooleanField()
    parent_comment_id = CharField(max_length=255, null=True)
    published_at = DateTimeField()
