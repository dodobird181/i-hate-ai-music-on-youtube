from dataclasses import asdict
from logging import getLogger
from time import perf_counter

from lightgbm import Booster
from pandas import DataFrame
from peewee import fn

from feature_extraction import extract
from models import Comment, Video

logger = getLogger(__name__)


class VideoLabeler:

    MODEL_PATH = "video_model.txt"

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            logger.info(f"Initializing AI Video prediction model from {cls.MODEL_PATH}...")
            start = perf_counter()
            cls._instance = Booster(model_file="video_model.txt")
            end = perf_counter()
            logger.info(f"Finished initializing {cls.MODEL_PATH} after {end - start:.6f} seconds.")
        return cls._instance


def predict(video, threshold=0.7) -> Video.Label:

    comments = Comment.select().where(Comment.video == video.id)
    features = extract(video, comments)
    video_data = asdict(features.description) | asdict(features.comments)
    pred_category = VideoLabeler().predict(DataFrame([video_data]))

    if float(pred_category[0]) >= threshold:  # type: ignore
        return Video.Label.HUMAN
    return Video.Label.AI


videos = [
    x
    for x in Video.select()
    .where((Video.duration_seconds > 60) & (Video.comments >= 50))
    .order_by(fn.Random())
    .limit(100)
]
for video in videos:
    start = perf_counter()
    pred = predict(video)
    end = perf_counter()
    logger.info(
        f'Predicted video "{video.title}" by channel {video.channel_name} is {pred.name} in {end - start:.6f} seconds.'
    )
