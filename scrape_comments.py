from logging import getLogger

from src.models import Comment, Video
from src.youtube import OfficialYouTubeService

logger = getLogger()

videos = Video.select().where(
    (Video.duration_seconds > 60) & (Video.comments >= 50) & (Video.origin == Video.Origin.SCRAPED.value)
)
logger.info(
    "There are a total of {} videos eligible for training in the database. Of those, {} are human and {} are AI.".format(
        videos.count(),
        videos.where(Video.label == Video.Label.HUMAN.value).count(),
        videos.where(Video.label == Video.Label.AI.value).count(),
    )
)
already_scraped = []
need_scraping = []
for video in videos:
    if Comment.select().where(Comment.video == video.id).count() == 0:
        need_scraping.append(video)
    else:
        already_scraped.append(video)
logger.info(
    "In the past, {} eligible videos have had comments previously scraped (will be skipped), and {} will be scraped momentarily...".format(
        len(already_scraped),
        len(need_scraping),
    )
)

youtube = OfficialYouTubeService.build_from_env(origin=Video.Origin.SCRAPED)
for video in need_scraping:
    comments = youtube.get_comments(video_id=video.id, max_results=100)
    print(f"Fetched {len(comments)} comments for video {video.id}.")
    for comment in comments:
        if Comment.filter(id=comment.id).select().count() == 0:
            comment.save(force_insert=True)
        else:
            comment.save()
