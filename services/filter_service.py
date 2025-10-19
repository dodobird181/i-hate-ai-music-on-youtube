import asyncio
import logging
from typing import List

from flask import Flask
from openai import AsyncOpenAI

from models.comment import Comment
from models.video import Video
from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class FilterService:

    def __init__(self, app: Flask, api_key: str, youtube_service):
        self.app = app
        self.client = AsyncOpenAI(api_key=api_key)
        self.youtube_service = youtube_service
        self.cache_service = CacheService()
        self.batch_size = 5
        self.max_comments = app.config["MAX_COMMENTS_TO_ASSESS_PER_VIDEO"]

        # Load blocklist from file on initialization
        blocklist_count = self.cache_service.load_blocklist_from_file()
        logger.info(f"Loaded {blocklist_count} channels into blocklist")

    def filter_videos(self, videos: List[Video]) -> List[Video]:
        """
        Blocking call to get filtered videos.
        """
        if not videos:
            return []
        filtered = asyncio.run(self._async_filter_videos(videos))
        return filtered

    def filter_videos_streaming(self, videos: List[Video]):
        """
        Generator that yields videos as they pass filtering.
        Processes in batches but yields results immediately.
        """
        if not videos:
            return

        async def process_batch(batch_videos):
            tasks = []
            for video in batch_videos:
                comments = self.youtube_service.get_comments(video.id, self.max_comments)
                tasks.append(self._check_video(video, comments))
            return await asyncio.gather(*tasks)

        for i in range(0, len(videos), self.batch_size):
            batch = videos[i : i + self.batch_size]
            batch_results = asyncio.run(process_batch(batch))

            for video, is_human in batch_results:
                if is_human:
                    yield video

    async def _async_filter_videos(self, videos: List[Video]) -> List[Video]:
        tasks = []
        for video in videos:
            comments = self.youtube_service.get_comments(video.id, self.max_comments)
            tasks.append(self._check_video(video, comments))

        results = []
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i : i + self.batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)

        return [video for video, is_human in results if is_human]

    async def _check_video(self, video: Video, comments: List[Comment]) -> tuple[Video, bool]:
        # Check blocklist first
        if self.cache_service.is_channel_blocklisted(video.channel.id):
            logger.info(
                f"{video} from blocklisted channel {video.channel.title} ({video.channel.id}), filtering out..."
            )
            self.cache_service.cache_result(video.id, 0, False)
            return video, False

        # Check cache
        cached_result = self.cache_service.get_cached_result(video.id)
        if cached_result is not None:
            humanity_score, is_human = cached_result
            logger.info(f"Using cached result for {video}: score={humanity_score}, is_human={is_human}")
            return video, is_human

        if not comments:
            logger.info(f"No comments found for video {video}, filtering out...")
            self.cache_service.cache_result(video.id, 0, False)
            return video, False

        if video.contains_synthetic_media:
            logger.info(f"{video} flagged by it's creator as AI (thanks bro), filtering out...")
            self.cache_service.cache_result(video.id, 0, False)
            return video, False

        with open("QUERY.md", "r") as f:
            prompt_template = f.read()

        comment_threshold = self.app.config["EXCLUDE_VIDEOS_UNDER_N_COMMENTS"]
        if len(comments) < comment_threshold:
            logger.info(f"Num comments for video {video} under threshold {comment_threshold}, filtering out...")
            self.cache_service.cache_result(video.id, 0, False)
            return video, False

        prompt = prompt_template.format(
            description=video.description, comments="\n".join([str(x) for x in comments])
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-mini-2025-08-07",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI-music detection assistant. Respond with only a number between 0 and 100 (inclusive). E.g., '42'.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            content = response.choices[0].message.content
            if not content:
                logger.warning(f"Empty response for video {video.id}")
                self.cache_service.cache_result(video.id, 0, False)
                return video, False

            result = content.strip()
            humanity_score = int(result)
            is_human = humanity_score >= 90

            logger.info(f"{video}'s humanity score is: {humanity_score}")

            # Cache the result
            self.cache_service.cache_result(video.id, humanity_score, is_human)

            return video, is_human

        except Exception as e:
            logger.error(f"Error checking video {video}: {e}")
            return video, False
