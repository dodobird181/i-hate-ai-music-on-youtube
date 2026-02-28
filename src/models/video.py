from enum import Enum

from peewee import BooleanField, CharField, DateTimeField, IntegerField, TextField

from . import BaseModel


class Video(BaseModel):

    class Label(Enum):
        UNLABELLED = "unlabelled"
        HUMAN = "human"
        AI = "ai"

    class Origin(Enum):
        # Scraped from youtube (usually labeled by the scraper)
        SCRAPED = "scraped"
        # Video came from the app, so trust the label less and probably
        # will want to exclude from training.
        APP = "app"

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
    origin = CharField(max_length=255)
    duration_seconds = IntegerField()
    published_at = DateTimeField()
