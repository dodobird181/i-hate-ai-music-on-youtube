import json
from dataclasses import dataclass
from enum import Enum

from models import Channel, db_conn, fill_from, find_none_paths


@dataclass
class Video:
    """
    A youtube video.
    """

    class ParseError(Exception):
        """
        There was an error while trying to parse raw data
        from youtube's API into a `Video` object.
        """

        def __init__(self, raw_data: str, errors: list[str]):
            self.raw_data = raw_data
            self.errors = errors
            super().__init__()

        def __str__(self):
            return f"{self.raw_data}, with errors: {self.errors}."

    @dataclass
    class Statistics:
        """
        A youtube video's statistics.
        """

        views: int
        likes: int
        favorites: int
        comments: int

    class Label(Enum):
        """
        Label for supervised learning (does NOT come from youtube).
        """

        UNLABELLED = "unlabelled"
        HUMAN = "human"
        AI = "ai"

    id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    channel: Channel
    stats: Statistics
    is_livestream: bool
    contains_synthetic_media: bool
    label: Label

    @classmethod
    def from_data(cls, data: dict) -> "Video":

        # What the video data should look like. The None values are required, and any other value is a default.
        data_template = {
            "id": None,
            "snippet": {
                "title": None,
                "description": None,
                "thumbnails": {
                    "medium": {
                        "url": None,
                    },
                },
                "channelId": None,
                "channelTitle": None,
            },
            "statistics": {
                "viewCount": None,
                "likeCount": None,
                "favoriteCount": None,
                "commentCount": None,
            },
            # True if the video is a live-stream
            "liveStreamingDetails": False,
            "status": {
                # True if video is self-reported as AI
                "containsSyntheticMedia": False,
            },
            # Whether we have labelled this video as human-made, or AI, for ML-model training purposes.
            "label": cls.Label.UNLABELLED.value,
        }

        # Fill the data template and raise on any leftover None(s)
        data = fill_from(data, data_template)
        none_paths = find_none_paths(data)
        if len(none_paths) > 0:
            raise cls.ParseError(json.dumps(data, indent=2), [f"Path {p} cannot be None!" for p in none_paths])

        video_id = None
        if isinstance(data["id"], str):
            # Youtube's Videos API returns video IDs as a string.
            video_id = data["id"]
        elif isinstance(data["id"], dict) and "videoId" in data["id"]:
            # Youtube's Search API returns video IDs in a second nested dictionary.
            video_id = data["id"]["videoId"]
        else:
            raise cls.ParseError(json.dumps(data, indent=2), ["Could not parse video_id from data!"])

        return cls(
            id=str(video_id),
            title=str(data["snippet"]["title"]),
            description=str(data["snippet"]["description"]),
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=str(data["snippet"]["thumbnails"]["medium"]["url"]),
            channel=Channel(
                id=str(data["snippet"]["channelId"]),
                title=str(data["snippet"]["channelTitle"]),
            ),
            stats=cls.Statistics(
                views=int(data["statistics"]["viewCount"]),
                likes=int(data["statistics"]["likeCount"]),
                favorites=int(data["statistics"]["favoriteCount"]),
                comments=int(data["statistics"]["commentCount"]),
            ),
            is_livestream=bool("liveStreamingDetails" in data),
            contains_synthetic_media=data["status"]["containsSyntheticMedia"],
            label=cls.Label(data["label"]),
        )

    def save(self) -> None:
        with db_conn() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                    INSERT OR REPLACE INTO videos
                    (
                        video_id,
                        title,
                        description,
                        url,
                        thumbnail_url,
                        channel_id,
                        channel_title,
                        views,
                        likes,
                        favorites,
                        comments,
                        is_livestream,
                        contains_synthetic_media,
                        label
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.id,
                    self.title,
                    self.description,
                    self.url,
                    self.thumbnail_url,
                    self.channel.id,
                    self.channel.title,
                    self.stats.views,
                    self.stats.likes,
                    self.stats.favorites,
                    self.stats.comments,
                    self.is_livestream,
                    self.contains_synthetic_media,
                    self.label.value,
                ),
            )
            connection.commit()

    def from_db(self, id: str) -> "Video": ...

    def __str__(self) -> str:
        return '<Video: "{}", by {}>'.format(self.title, self.channel.title)
