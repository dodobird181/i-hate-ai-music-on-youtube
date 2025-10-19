import json
import logging
from typing import List

from googleapiclient.discovery import build

from models.video import Video

logger = logging.getLogger(__name__)


class YouTubeService:

    def __init__(self, api_key: str):
        self.youtube = build("youtube", "v3", developerKey=api_key)

    def search_videos(self, query: str, max_results=20) -> List[Video]:
        """
        Search youtube and return a list of videos.
        """
        videos_response = (
            self.youtube.search()
            .list(
                q=query,
                type="video",
                part="snippet",
                maxResults=max_results,
                videoCategoryId="10",
                fields="items(id/videoId,snippet(publishedAt,channelId,channelTitle,title,thumbnails/medium/url))",
            )
            .execute()
        )
        videos = []
        for item in videos_response.get("items", []):
            try:
                video = Video.from_data(item)
                videos.append(video)
            except Video.ParseError as e:
                logger.error(f"Failed to parse video data: {e}")
                continue
            finally:
                logger.debug(
                    "YouTubeService found: {}.".format(
                        json.dumps(
                            {
                                "num_videos": len(videos),
                                "videos": [str(x) for x in videos],
                            },
                            indent=2,
                        ),
                    )
                )
        return videos

    def get_comments(self, video_id: str, max_results=100):
        try:
            comments_response = (
                self.youtube.commentThreads()
                .list(videoId=video_id, part="snippet", maxResults=max_results, order="relevance")
                .execute()
            )
            comments = [
                item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
                for item in comments_response.get("items", [])
            ]
            breakpoint()
            return comments
        except Exception:
            return []
