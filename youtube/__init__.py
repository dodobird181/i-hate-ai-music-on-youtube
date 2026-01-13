from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from models import Comment, Video


class BaseYoutubeService(ABC):

    class YoutubeError(Exception): ...

    class NotFoundError(YoutubeError): ...

    class ParseError(Exception):
        """
        Something went wrong while parsing raw data from youtube.
        """

        def __init__(self, raw_data: str, errors: list[str]):
            self.raw_data = raw_data
            self.errors = errors
            super().__init__()

        def __str__(self):
            return f"{self.raw_data}, with errors: {self.errors}."

    class ChannelNotFound(NotFoundError): ...

    class PlaylistNotFound(NotFoundError): ...

    class VideoParseError(ParseError): ...

    class CommentParseError(ParseError): ...

    @abstractmethod
    def search_videos(
        self,
        query: str,
        max_results=20,
        page_token: Optional[str] = None,
    ) -> Tuple[List[Video], Optional[str]]:
        """
        Send a search query to youtube and return a list of videos.
        """
        ...

    @abstractmethod
    def get_channel_videos(self, channel_id: str, max_videos: int = 10) -> List[Video]:
        """
        Get some videos associated with a channel on youtube.
        """
        ...

    @abstractmethod
    def get_comments(self, video_id: str, max_results: int) -> List[Comment]:
        """
        Get the most recent comments on a youtube video.
        """
        ...


def fill_from(source: dict, template: dict) -> dict:
    """
    Traverse `template` and fill its values using matching keys from `source`.
    """
    result = {}

    for key, template_value in template.items():
        if isinstance(template_value, dict):
            # Recurse if both sides are dicts
            source_value = source.get(key, {})
            if isinstance(source_value, dict):
                result[key] = fill_from(source_value, template_value)
            else:
                result[key] = fill_from({}, template_value)
        else:
            # Leaf node
            result[key] = source.get(key, template.get(key, None))

    return result


def find_none_paths(obj: dict, _path: str = "") -> List[str]:
    """
    Find all paths leading to None. E.g. {"foo": {"bar": None}} -> ["foo.bar"]
    """

    paths: List[str] = []

    if obj is None:
        paths.append(_path)
        return paths

    if isinstance(obj, dict):
        for k, v in obj.items():
            paths.extend(find_none_paths(v, f"{_path}.{k}" if _path else k))

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            paths.extend(find_none_paths(v, f"{_path}[{i}]"))

    return paths


from youtube.mock_service import MockYoutubeService
from youtube.official_service import OfficialYouTubeService
