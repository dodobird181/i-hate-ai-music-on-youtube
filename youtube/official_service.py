import json
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from isodate import parse_duration

from models import Comment, Video

from . import BaseYoutubeService, fill_from, find_none_paths

logger = logging.getLogger(__name__)


class OfficialYouTubeService(BaseYoutubeService):

    @classmethod
    def _video_from_data(cls, data: dict) -> Video:

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
            "label": Video.Label.UNLABELLED.value,
        }

        # Fill the data template and raise on any leftover None(s)
        data = fill_from(data, data_template)
        none_paths = find_none_paths(data)
        if len(none_paths) > 0:
            raise cls.VideoParseError(json.dumps(data, indent=2), [f"Path {p} cannot be None!" for p in none_paths])

        video_id = None
        if isinstance(data["id"], str):
            # Youtube's Videos API returns video IDs as a string.
            video_id = data["id"]
        elif isinstance(data["id"], dict) and "videoId" in data["id"]:
            # Youtube's Search API returns video IDs in a second nested dictionary.
            video_id = data["id"]["videoId"]
        else:
            raise cls.VideoParseError(json.dumps(data, indent=2), ["Could not parse video_id from data!"])

        return Video(
            id=str(video_id),
            title=str(data["snippet"]["title"]),
            description=str(data["snippet"]["description"]),
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=str(data["snippet"]["thumbnails"]["medium"]["url"]),
            channel_id=str(data["snippet"]["channelId"]),
            channel_name=str(data["snippet"]["channelTitle"]),
            views=int(data["statistics"]["viewCount"]),
            likes=int(data["statistics"]["likeCount"]),
            favorites=int(data["statistics"]["favoriteCount"]),
            comments=int(data["statistics"]["commentCount"]),
            is_livestream=bool("liveStreamingDetails" in data),
            contains_synthetic_media=data["status"]["containsSyntheticMedia"],
            label=Video.Label(data["label"]),
            duration_seconds=int(parse_duration(data["contentDetails"]["duration"]).total_seconds()),
            published_at=datetime.fromisoformat(data["snippet"]["publishedAt"].replace("Z", "+00:00")),
        )

    @classmethod
    def _comment_from_data(cls, data: dict) -> Video: ...

    def __init__(self, api_key: str):
        self.youtube = build("youtube", "v3", developerKey=api_key)

    def search_videos(
        self, query: str, max_results=20, page_token: Optional[str] = None
    ) -> Tuple[List[Video], Optional[str]]:
        """
        Search youtube and return a list of videos along with the next page token.
        Returns: (videos, next_page_token)
        """
        request_params = {
            "q": query,
            "type": "video",
            "part": "snippet",
            "maxResults": max_results,
            "videoCategoryId": "10",  # means in the music category
            "fields": "items(id/videoId,snippet(publishedAt,channelId,channelTitle,title,description,thumbnails/medium/url)),nextPageToken,contentDetails(duration)",
        }
        if page_token:
            request_params["pageToken"] = page_token

        videos_response = self.youtube.search().list(**request_params).execute()
        videos = []
        for item in videos_response.get("items", []):
            try:
                video = self._video_from_data(item)
                videos.append(video)
            except self.VideoParseError as e:
                logger.error(f"Failed to parse video data: {e}")
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
        next_page_token = videos_response.get("nextPageToken")
        return videos, next_page_token

    def get_channel_videos(self, channel_id: str, max_videos: int = 10) -> List[Video]:
        """
        Get any uploaded videos from a channel.
        """

        # 1. Get uploads playlist
        request = self.youtube.channels().list(part="contentDetails", id=channel_id)
        response = request.execute()
        if "items" not in response:
            raise self.ChannelNotFound()
        uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        video_ids = []
        next_page_token = None

        # 2. Collect video IDs from the playlist
        while True:
            request_params = {
                "part": "snippet",
                "playlistId": uploads_playlist_id,
                "maxResults": min(max_videos, 50),  # playlistItems max is 50 per page
                "pageToken": next_page_token,
                "fields": "items/snippet/resourceId/videoId,nextPageToken",
            }
            try:
                request = self.youtube.playlistItems().list(**request_params)
                response = request.execute()
            except HttpError as e:
                if hasattr(e, "error_details") and isinstance(e.error_details, list):
                    if e.error_details[0]["reason"] == "playlistNotFound":
                        raise self.PlaylistNotFound() from e
                raise e

            for item in response.get("items", []):
                video_ids.append(item["snippet"]["resourceId"]["videoId"])
                if len(video_ids) >= max_videos:
                    break

            if len(video_ids) >= max_videos:
                break

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        videos: List[Video] = []

        # 3. Fetch full video details in batches of 50
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i : i + 50]
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics,liveStreamingDetails,status", id=",".join(batch_ids)
            )
            response = request.execute()

            for item in response.get("items", []):
                try:
                    video = self._video_from_data(item)
                    videos.append(video)
                except self.VideoParseError as e:
                    logger.error(f"Failed to parse video data: {e}")

        return videos[:max_videos]

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
            if e.__dict__["error_details"][0]["reason"] == "commentsDisabled":
                # It's expected that we will sometimes hit videos with comments disabled...
                return []
            logger.error(f"Error fetching comments for video {video_id}.", exc_info=e)
            return []
