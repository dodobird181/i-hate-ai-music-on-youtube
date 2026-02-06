import json
import logging
from dataclasses import dataclass
from datetime import datetime
from os import getenv
from typing import Any, List, Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from isodate import parse_duration

from models import Comment, Video

from . import fill_from, find_none_paths

logger = logging.getLogger(__name__)


class OfficialYouTubeService:

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

    class API:
        """
        Each subclass here represents a different youtube API query.
        """

        class Search:

            @staticmethod
            def execute(youtube: Any, query: str, max_results=20, page_token: Optional[str] = None) -> dict:
                if max_results > 50 or max_results < 0:
                    raise ValueError(f"max_results must be in [0, 50]")
                return (
                    youtube.search().list(
                        q=query,
                        type="video",
                        part="snippet",
                        maxResults=max_results,
                        fields=("items(id/videoId),nextPageToken"),
                        pageToken=page_token,
                        # "videoCategoryId": "10",  # Music
                    )
                ).execute()

            @dataclass
            class Response:
                video_ids: List[str]
                next_page_token: Optional[str]

        class Videos:

            @staticmethod
            def execute(youtube: Any, video_ids: List[str]) -> dict:
                return (
                    youtube.videos()
                    .list(
                        part="contentDetails,statistics,snippet",
                        id=",".join(video_ids),
                        # fields=(
                        #     "items(id,contentDetails/duration,statistics(viewCount,likeCount,favoriteCount,commentCount),snippet(publishedAt,channelId,channelTitle,title,description,thumbnails/medium/url)))"
                        # ),
                    )
                    .execute()
                )

            @dataclass
            class Response:
                videos: List[Video]
                next_page_token: Optional[str]

        class PlaylistItems:

            @dataclass
            class Response:
                video_ids: List[str]
                next_page_token: Optional[str]

        class Channels:

            @dataclass
            class Response: ...

        class CommentThreads:

            @dataclass
            class Response: ...

    @classmethod
    def build_from_env(cls, origin: Video.Origin) -> "OfficialYouTubeService":

        # Get API key from env
        load_dotenv()
        KEY_NAME = "YOUTUBE_API_KEY"
        key = getenv(KEY_NAME)
        if key is None:
            raise ValueError(f"Expected {KEY_NAME} to exist in the environment!")

        return cls(api_key=key, origin=origin)

    def __init__(self, api_key: str, origin: Video.Origin):
        self.youtube = build("youtube", "v3", developerKey=api_key)
        self.origin = origin

    def _video_from_data(self, data: dict) -> Video:

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
                "viewCount": 0,
                "likeCount": 0,
                "favoriteCount": 0,
                "commentCount": 0,
            },
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
            raise self.VideoParseError(
                json.dumps(data, indent=2), [f"Path {p} cannot be None!" for p in none_paths]
            )

        video_id = None
        if isinstance(data["id"], str):
            # Youtube's Videos API returns video IDs as a string.
            video_id = data["id"]
        elif isinstance(data["id"], dict) and "videoId" in data["id"]:
            # Youtube's Search API returns video IDs in a second nested dictionary.
            video_id = data["id"]["videoId"]
        else:
            raise self.VideoParseError(json.dumps(data, indent=2), ["Could not parse video_id from data!"])

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
            label=data["label"],
            duration_seconds=int(parse_duration(data["contentDetails"]["duration"]).total_seconds()),
            published_at=datetime.fromisoformat(data["snippet"]["publishedAt"].replace("Z", "+00:00")),
            origin=self.origin.value,
        )

    @classmethod
    def _comment_from_data(cls, data: dict, video: Video) -> Comment:

        NO_PARENT = "NO_PARENT"

        # What the comment data should look like. The None values are required, and any other value is a default.
        data_template = {
            "id": None,
            "snippet": {
                "textOriginal": None,
                "authorDisplayName": None,
                "authorChannelId": {"value": None},
                "videoId": None,
                "publishedAt": None,
                "parentId": NO_PARENT,
                "likeCount": 0,
            },
        }

        # Fill the data template and raise on any leftover None(s)
        data = fill_from(data, data_template)
        none_paths = find_none_paths(data)
        if len(none_paths) > 0:
            raise cls.VideoParseError(json.dumps(data, indent=2), [f"Path {p} cannot be None!" for p in none_paths])

        # Set isReply based on whether the comment has a parent
        if data["snippet"]["parentId"] == NO_PARENT:
            data["snippet"]["parentId"] = None
            data["snippet"]["isReply"] = False
        else:
            data["snippet"]["isReply"] = True

        return Comment(
            id=str(data["id"]),
            text=str(data["snippet"]["textOriginal"]),
            video=video,
            author_channel_id=str(data["snippet"]["authorChannelId"]["value"]),
            author_display_name=str(data["snippet"]["authorDisplayName"]),
            likes=int(data["snippet"]["likeCount"]),
            is_reply=bool(data["snippet"]["isReply"]),
            parent_comment_id=data["snippet"]["parentId"],  # No str conversion because it may be None
            published_at=datetime.fromisoformat(data["snippet"]["publishedAt"].replace("Z", "+00:00")),
        )

    def search(
        self,
        query: str,
        max_results=20,
        page_token: Optional[str] = None,
    ) -> API.Search.Response:
        """
        Search youtube and get a paginated list of video IDs.
        """

        response = self.API.Search.execute(
            self.youtube,
            query,
            max_results,
            page_token,
        )

        video_ids = []
        next_page_token = None
        if "items" in response:

            # Collect video IDs
            for item in response["items"]:
                if "id" in item and "videoId" in item["id"]:
                    video_ids.append(item["id"]["videoId"])

        # Collect next page token
        if "nextPageToken" in response:
            next_page_token = response["nextPageToken"]

        return self.API.Search.Response(video_ids, next_page_token)

    def _videos_from_videos_response(self, response: dict) -> List[Video]:

        videos: List[Video] = []
        if "items" in response:
            for item in response["items"]:
                try:
                    video = self._video_from_data(item)
                    videos.append(video)
                except self.VideoParseError as e:
                    logger.error(f"Failed to parse video data!", exc_info=e)

        return videos

    def videos(
        self,
        query: str,
        max_results: int = 20,
        page_token: Optional[str] = None,
    ) -> API.Videos.Response:
        """
        Search youtube and get a paginated list of videos.
        """
        search_response = self.search(query, max_results, page_token)
        videos_response = self.API.Videos.execute(self.youtube, search_response.video_ids)
        videos = self._videos_from_videos_response(videos_response)
        return self.API.Videos.Response(videos, search_response.next_page_token)

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
        """
        Get comments from a video, specifying the maximum number of top-level comments to be returned.
        """
        try:
            video = Video.get(id=video_id)
            comments_response = (
                self.youtube.commentThreads()
                .list(videoId=video_id, part="snippet,replies", maxResults=max_results, order="relevance")
                .execute()
            )
            comments = []
            for item in comments_response.get("items", []):

                comment = self._comment_from_data(item["snippet"]["topLevelComment"], video)
                comments.append(comment)

                if "replies" in item:
                    # Grab replies that are 1 "layer" deep as well...
                    for reply in item["replies"]["comments"]:
                        comment = self._comment_from_data(reply, video)
                        comments.append(comment)

            return comments
        except Exception as e:
            if "error_details" in e.__dict__ and e.__dict__["error_details"][0]["reason"] == "commentsDisabled":
                # It's expected that we will sometimes hit videos with comments disabled...
                logger.info(f"Could not fetch comments for video {video_id}, the video has comments disabled.")
                return []
            logger.error(f"Could not fetch comments for video {video_id}.", exc_info=e)
            return []
