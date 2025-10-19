import json
from dataclasses import dataclass
from typing import Any, Dict

from models import Channel


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

        ...

    @dataclass
    class Statistics:
        """
        A youtube video's statistics.
        """

        views: int
        likes: int
        favorites: int
        comments: int

    id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    channel: Channel
    stats: Statistics
    is_livestream: bool
    contains_synthetic_media: bool

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "Video":
        raw_id = data.get("id")
        if isinstance(raw_id, dict):
            # Search API returns video IDs in a second nested dictionary...
            id = str(raw_id.get("videoId", None))
        else:
            # Videos API returns video IDs as a simple string
            id = str(raw_id)

        snippet = data.get("snippet", None)
        if not snippet:
            raise cls.ParseError("Expected a 'snippet' key in video data: {}.".format(json.dumps(data, indent=2)))

        title = str(snippet.get("title", None))
        description = str(snippet.get("description", ""))
        thumbnail_url = snippet.get("thumbnails", {}).get("medium", {}).get("url", None)
        channel_id = snippet.get("channelId", None)
        channel_title = snippet.get("channelTitle", None)

        statistics = data.get("statistics", {})
        views = int(statistics.get("viewCount", 0))
        likes = int(statistics.get("likeCount", 0))
        favorites = int(statistics.get("favoriteCount", 0))
        comments = int(statistics.get("commentCount", 0))

        status = data.get("status", {})
        contains_synthetic_media = status.get("containsSyntheticMedia", False)
        is_livestream = "liveStreamingDetails" in data

        if not all([id, title, thumbnail_url, channel_id, channel_title]):
            raise cls.ParseError("Missing required fields in video data: {}.".format(json.dumps(data, indent=2)))

        return cls(
            id=id,
            title=title,
            description=description,
            url=f"https://www.youtube.com/watch?v={id}",
            thumbnail_url=thumbnail_url,
            channel=Channel(id=channel_id, title=channel_title),
            stats=cls.Statistics(views=views, likes=likes, favorites=favorites, comments=comments),
            is_livestream=is_livestream,
            contains_synthetic_media=contains_synthetic_media,
        )

    def __str__(self) -> str:
        return '<Video: "{}", by {}>'.format(self.title, self.channel.title)
