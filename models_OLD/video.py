import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import isodate

from models import Channel, fill_from, find_none_paths


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

    class DoesNotExist(Exception):
        """
        The video does not exist in the database.
        """

        def __init__(self, id: str):
            self.id = id
            super().__init__()

        def __str__(self):
            return f"Video with id '{self.id}' does not exist."

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
    duration_seconds: int
    published_at: datetime

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
                "publishedAt": None,
            },
            "statistics": {
                "viewCount": None,
                "likeCount": None,
                "favoriteCount": None,
                "commentCount": None,
            },
            # duration_iso = response["items"][0]["contentDetails"]["duration"]
            "contentDetails": {
                "duration": None,
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
            duration_seconds=int(isodate.parse_duration(data["contentDetails"]["duration"]).total_seconds()),
            published_at=datetime.fromisoformat(data["snippet"]["publishedAt"].replace("Z", "+00:00")),
        )

    def save(self, write=blocking_write) -> None:
        write(
            "execute",
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
                    label,
                    duration_seconds,
                    published_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                self.duration_seconds,
                self.published_at.isoformat(),
            ),
        )

    @classmethod
    def from_db(cls, id: str) -> "Video":
        with readonly_conn() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM videos WHERE video_id = ?", (id,))
            row = cursor.fetchone()

            if row is None:
                raise Video.DoesNotExist(id)

            return Video(
                id=row["video_id"],
                title=row["title"],
                description=row["description"],
                url=row["url"],
                thumbnail_url=row["thumbnail_url"],
                channel=Channel(
                    id=row["channel_id"],
                    title=row["channel_title"],
                ),
                stats=cls.Statistics(
                    views=row["views"],
                    likes=row["likes"],
                    favorites=row["favorites"],
                    comments=row["comments"],
                ),
                is_livestream=row["is_livestream"],
                contains_synthetic_media=row["contains_synthetic_media"],
                label=cls.Label(row["label"]),
                duration_seconds=row["duration_seconds"],
                published_at=datetime.fromisoformat(row["published_at"]),
            )

    @classmethod
    def count(cls) -> int:
        with readonly_conn() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            return int(cursor.fetchone()[0])

    def __str__(self) -> str:
        return '<Video: "{}", by {}>'.format(self.title, self.channel.title)
