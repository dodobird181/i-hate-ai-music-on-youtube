import asyncio
import logging
from typing import List

from openai import AsyncOpenAI

from models.video import Video

logger = logging.getLogger(__name__)


class FilterService:

    def __init__(self, api_key: str, youtube_service):
        self.client = AsyncOpenAI(api_key=api_key)
        self.youtube_service = youtube_service
        self.batch_size = 5

    def filter_videos(self, videos: List[Video]) -> List[Video]:
        """
        Blocking call to get filtered videos.
        """
        if not videos:
            return []
        filtered = asyncio.run(self._async_filter_videos(videos))
        return filtered

    async def _async_filter_videos(self, videos: List[Video]) -> List[Video]:
        tasks = []
        for video in videos:
            comments = self.youtube_service.get_comments(video.id)
            tasks.append(self._check_video(video, comments))

        results = []
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i : i + self.batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)

        return [video for video, is_human in results if is_human]

    async def _check_video(self, video: Video, comments: List[str]) -> tuple[Video, bool]:
        if not comments:
            logger.warning(f"No comments found for video {video.id}, filtering out")
            return video, False

        with open("QUERY.md", "r") as f:
            prompt_template = f.read()

        comments_text = "\n".join(comments[:50])
        prompt = prompt_template.format(
            video_title=video.title, channel_name=video.channel.title, comments=comments_text
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI detection assistant. Respond with only 'HUMAN' or 'AI'.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=10,
            )

            content = response.choices[0].message.content
            if not content:
                logger.warning(f"Empty response for video {video.id}")
                return video, False

            result = content.strip().upper()
            is_human = result == "HUMAN"
            logger.info(f"Video {video.id} classified as: {result}")
            return video, is_human
        except Exception as e:
            logger.error(f"Error checking video {video.id}: {e}")
            return video, False
