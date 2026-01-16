from models import Comment, Video
from youtube import OfficialYouTubeService

videos = Video.select().where((Video.duration_seconds > 60) & (Video.comments >= 50))
youtube = OfficialYouTubeService.build_from_env()

for video in videos:
    comments = youtube.get_comments(video_id=video.id, max_results=100)
    print(f"Fetched {len(comments)} comments for video {video.id}.")
    for comment in comments:
        if Comment.filter(id=comment.id).select().count() == 0:
            comment.save(force_insert=True)
        else:
            comment.save()
