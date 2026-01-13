from typing import List, Optional, Tuple

from models import Comment, Video

from . import BaseYoutubeService


class MockYoutubeService(BaseYoutubeService):

    def search_videos(
        self,
        query: str,
        max_results=20,
        page_token: Optional[str] = None,
    ) -> Tuple[List[Video], Optional[str]]:
        """
        Send a search query to youtube and return a list of videos.
        """
        raise NotImplementedError

    def get_channel_videos(self, channel_id: str, max_videos: int = 10) -> List[Video]:
        """
        Get some videos associated with a channel on youtube.
        """
        raise NotImplementedError

    def get_comments(self, video_id: str, max_results: int) -> List[Comment]:
        """
        Get the most recent comments on a youtube video.
        """
        raise NotImplementedError
