import os

import dotenv

from ai_channels import CHANNELS
from models import Video
from services_OLD.youtube_service import YouTubeService

# Get API key from env
dotenv.load_dotenv()
KEY_NAME = "YOUTUBE_API_KEY"
key = os.getenv(KEY_NAME)
if key is None:
    raise ValueError(f"Expected {KEY_NAME} to exist in the environment!")

CHANNELS = ["UCm9HA7dFbnkBmYweSt-6D4g"]

# Test scrape videos
for channel_id in CHANNELS:
    youtube_service = YouTubeService(api_key=key)
    try:
        videos = youtube_service.get_channel_videos(channel_id=channel_id, max_videos=100)
        print(f"Collected {len(videos)} videos from channel {channel_id}.")
        for video in videos:
            video.label = Video.Label.HUMAN
            video.save()
    except YouTubeService.ChannelNotFound:
        print(f"Channel not found: {channel_id}.")
        continue
    except YouTubeService.PlaylistNotFound:
        print(f"Playlist not found for channel: {channel_id}.")
        continue
