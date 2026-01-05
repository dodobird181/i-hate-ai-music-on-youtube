import os

import dotenv

from services.youtube_service import YouTubeService

# Get API key from env
dotenv.load_dotenv()
KEY_NAME = "YOUTUBE_API_KEY"
key = os.getenv(KEY_NAME)
if key is None:
    raise ValueError(f"Expected {KEY_NAME} to exist in the environment!")

# Test scrape videos
channel_id = "UCyRbMM2KCivYQHnVi8y8AAw"
youtube_service = YouTubeService(api_key=key)
videos = youtube_service.get_channel_videos(channel_id=channel_id, max_videos=1)
print(f"Collected {len(videos)} videos from channel {channel_id}.")
print(videos)
