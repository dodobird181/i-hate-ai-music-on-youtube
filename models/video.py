from enum import Enum

from peewee import BooleanField, CharField, DateTimeField, IntegerField, TextField

from . import BaseModel


class Video(BaseModel):

    class Label(Enum):
        UNLABELLED = "unlabelled"
        HUMAN = "human"
        AI = "ai"

    id = CharField(primary_key=True, max_length=255)
    title = CharField(max_length=1024)
    description = TextField()
    url = CharField(max_length=2048)
    thumbnail_url = CharField(max_length=2048)
    channel_id = CharField(max_length=255)
    channel_name = CharField(max_length=1024)
    likes = IntegerField()
    comments = IntegerField()
    favorites = IntegerField()
    views = IntegerField()
    contains_synthetic_media = BooleanField()
    label = CharField(max_length=255, default=Label.UNLABELLED.value)
    duration_seconds = IntegerField()
    published_at = DateTimeField()
