from datetime import datetime, timezone

from googleapiclient.discovery import build


class YouTubeService:

    def __init__(self, api_key):
        self.youtube = build("youtube", "v3", developerKey=api_key)
        self.min_comment_threshold = 50
        self.pre_ai_cutoff_date = datetime(2022, 5, 1, tzinfo=timezone.utc)

    def search_videos(self, query, max_results=20):
        search_response = (
            self.youtube.search()
            .list(q=query, type="video", part="id,snippet", maxResults=max_results, videoCategoryId="10")
            .execute()
        )

        video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

        if not video_ids:
            return []

        videos_response = (
            self.youtube.videos()
            .list(id=",".join(video_ids), part="snippet,statistics,liveStreamingDetails,status")
            .execute()
        )

        videos = []
        for item in videos_response.get("items", []):
            video_data = self._parse_video(item)
            print(video_data)
            if video_data:
                videos.append(video_data)

        return videos

    def _parse_video(self, item):

        if "liveStreamingDetails" in item:
            return None

        status = item.get("status", {})
        if status.get("containsSyntheticMedia"):
            return None

        video_id = item["id"]
        snippet = item["snippet"]
        statistics = item.get("statistics", {})
        breakpoint()

        published_date = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
        comment_count = int(statistics.get("commentCount", 0))

        if published_date < self.pre_ai_cutoff_date:
            return {
                "video_id": video_id,
                "title": snippet["title"],
                "thumbnail": snippet["thumbnails"]["medium"]["url"],
                "channel": snippet["channelTitle"],
                "channel_id": snippet["channelId"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "pre_ai_era": True,
                "needs_filtering": False,
            }

        return {
            "video_id": video_id,
            "title": snippet["title"],
            "thumbnail": snippet["thumbnails"]["medium"]["url"],
            "channel": snippet["channelTitle"],
            "channel_id": snippet["channelId"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "comment_count": comment_count,
            "pre_ai_era": False,
            "needs_filtering": comment_count >= self.min_comment_threshold,
        }

    def get_comments(self, video_id, max_results=100):
        try:
            comments_response = (
                self.youtube.commentThreads()
                .list(videoId=video_id, part="snippet", maxResults=max_results, order="relevance")
                .execute()
            )

            comments = [
                item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                for item in comments_response.get("items", [])
            ]

            return comments
        except Exception:
            return []
