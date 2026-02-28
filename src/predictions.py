import json
from dataclasses import asdict
from logging import WARNING, getLogger
from time import perf_counter

from lightgbm import Booster
from pandas import DataFrame
from peewee import fn

from src.feature_extraction import extract
from src.models import Comment, Video

logger = getLogger(__name__)


class _VideoLabeler:

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
    pred_category = _VideoLabeler().predict(DataFrame([video_data]))

    logger.debug(f"Video {video.id} {video.title} by {video.channel_name} has humanity score of {pred_category[0]:0.2f}.")  # type: ignore
    logger.debug(json.dumps(video_data, indent=2))

    if float(pred_category[0]) >= threshold:  # type: ignore
        return Video.Label.HUMAN
    return Video.Label.AI


if __name__ == "__main__":

    def predict_dummy(video, threshold=0.7) -> dict:

        comments = Comment.select().where(Comment.video == video.id)
        features = extract(video, comments)
        video_data = asdict(features.description) | asdict(features.comments)
        return video_data

    logger.setLevel(WARNING)
    videos = [
        x
        for x in Video.select().where(
            (Video.duration_seconds > 60) & (Video.comments >= 50) & (Video.origin == Video.Origin.APP.value)
        )
        # .where(Video.id == "X0X12AD7nK4")
        .order_by(fn.Random()).limit(50)
    ]
    videos = [predict_dummy(x) for x in videos]
    avg = {k: sum(d[k] for d in videos) / len(videos) for k in videos[0]}
    print("Average APP feature-list:")
    print(avg)

    videos = [
        x
        for x in Video.select().where(
            (Video.duration_seconds > 60) & (Video.comments >= 50) & (Video.origin == Video.Origin.SCRAPED.value)
        )
        # .where(Video.id == "X0X12AD7nK4")
        .order_by(fn.Random()).limit(50)
    ]
    videos = [predict_dummy(x) for x in videos]
    avg = {k: sum(d[k] for d in videos) / len(videos) for k in videos[0]}
    print("Average SCRAPED feature-list:")
    print(avg)
