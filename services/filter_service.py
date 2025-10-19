import asyncio

from openai import AsyncOpenAI


class FilterService:

    def __init__(self, api_key, youtube_service):
        self.client = AsyncOpenAI(api_key=api_key)
        self.youtube_service = youtube_service
        self.batch_size = 5

    def filter_videos(self, videos):
        videos_needing_filter = [v for v in videos if v.get("needs_filtering", False)]
        pre_filtered_videos = [v for v in videos if not v.get("needs_filtering", False)]

        if not videos_needing_filter:
            return pre_filtered_videos

        filtered = asyncio.run(self._async_filter_videos(videos_needing_filter))
        return pre_filtered_videos + filtered

    async def _async_filter_videos(self, videos):

        tasks = []
        for video in videos:
            comments = self.youtube_service.get_comments(video["video_id"])
            tasks.append(self._check_video(video, comments))

        results = []
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i : i + self.batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)

        return [video for video, is_human in results if is_human]

    async def _check_video(self, video, comments):
        if not comments:
            return video, False

        with open("QUERY.md", "r") as f:
            prompt_template = f.read()

        comments_text = "\n".join(comments[:50])
        prompt = prompt_template.format(
            video_title=video["title"], channel_name=video["channel"], comments=comments_text
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

            result = response.choices[0].message.content.strip().upper()
            return video, result == "HUMAN"
        except Exception:
            return video, False
