from src.models import Video
from src.youtube import OfficialYouTubeService

# Scrape videos
for channel_id in [
    "UCLdqZBVvWa174TnYyLC-IAg",
    "UCqa_gEpx9XO7BoYkBD7kktQ",
    "UCJeBQabyLa_FvMxb6G67lkw",
    "UCLJpFgv7AUCLyMKFImVYymQ",
    "UCmey-edYKh4rJ6fn4albYIg",
    "UCN2GlHjuUD2KA6vh01rjn_Q",
    "UCR4P2JbCWZie0w6xQZJLDCQ",
    "UCm1AAvgMlMsUv49S9Qt2EDA",
    "UCr5v6l4EIKiImmJU-COJ0Sg",
    "UCFEXvJaxLUGJaCVxOGx8amw",
]:
    youtube = OfficialYouTubeService.build_from_env(origin=Video.Origin.SCRAPED)
    try:
        videos = youtube.get_channel_videos(channel_id=channel_id, max_videos=100)
        print(f"Collected {len(videos)} videos from channel {channel_id}.")
        for video in videos:
            video.label = Video.Label.HUMAN.value  # type: ignore
            if Video.filter(id=video.id).select().count() == 0:
                video.save(force_insert=True)
            else:
                video.save()
    except OfficialYouTubeService.ChannelNotFound:
        print(f"Channel not found: {channel_id}.")
        continue
    except OfficialYouTubeService.PlaylistNotFound:
        print(f"Playlist not found for channel: {channel_id}.")
        continue
