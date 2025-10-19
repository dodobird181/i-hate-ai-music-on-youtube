import json
import logging
from typing import List

from googleapiclient.discovery import build

from models.comment import Comment
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

    def get_comments(self, video_id: str, max_results: int) -> List[Comment]:
        try:
            comments_response = (
                self.youtube.commentThreads()
                .list(videoId=video_id, part="snippet,replies", maxResults=max_results, order="relevance")
                .execute()
            )
            comments = []
            for item in comments_response.get("items", []):
                top_level_comment = item["snippet"]["topLevelComment"]
                top_level_snippet = top_level_comment["snippet"]
                top_level_id = top_level_comment["id"]

                comments.append(
                    Comment(
                        text=top_level_snippet["textOriginal"],
                        is_reply=False,
                        comment_id=top_level_id,
                        author=top_level_snippet.get("authorDisplayName", ""),
                        parent_id=None,
                    )
                )
                if "replies" in item:
                    # Grab replies that are 1 "layer" deep as well...
                    for reply in item["replies"]["comments"]:
                        reply_snippet = reply["snippet"]
                        comments.append(
                            Comment(
                                text=reply_snippet["textOriginal"],
                                is_reply=True,
                                comment_id=reply["id"],
                                author=reply_snippet.get("authorDisplayName", ""),
                                parent_id=reply_snippet.get("parentId", top_level_id),
                            )
                        )
            return comments
        except Exception as e:
            if "has disabled comments" in str(e):
                # Expected that we will sometimes hit videos that have comments disabled...
                pass
            logger.error(f"Error fetching comments for video {video_id}: {e}")
            return []
