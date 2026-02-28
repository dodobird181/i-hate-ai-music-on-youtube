from dataclasses import asdict
from logging import getLogger
from time import perf_counter
from typing import Callable

import pandas as pd
from lightgbm import Dataset, plot_importance, train
from matplotlib import pyplot
from numpy import array, int8
from pandas import DataFrame, read_csv
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.embeddings import VideoDescriptionEmbedding
from src.feature_extraction import extract
from src.models import Comment, Video

logger = getLogger(__name__)


def process_videos(videos: list[Video], filename: str) -> None:

    processed_videos = []

    for i, video in enumerate(videos):
        print(f"Processing video {i} of {len(videos)}...")
        comments = Comment.select().where(Comment.video == video.id)
        features = extract(video, comments)
        video_data = (
            asdict(features.description)
            | asdict(features.comments)
            | {"label": video.label, "video_id": str(video.id)}
        )
        processed_videos.append(video_data)

    df = DataFrame(processed_videos)
    with open(filename, "w") as file:
        file.write(df.to_csv())


def train_model():
    DATA_PATH = "joey_data.csv"

    logger.info("Loading training data...")
    start = perf_counter()
    data = read_csv(DATA_PATH, header=0)
    end = perf_counter()
    logger.info(f"Finished loading {DATA_PATH} after {end - start:.6f} seconds.")

    breakpoint()

    X = data.drop(columns=["label"])
    if "Unnamed: 0" in data:
        # index row for data
        X = data.drop(columns=["Unnamed: 0", "label"])

    label_map = {
        "human": 1,
        "ai": 0,
    }

    y = data["label"].map(label_map).astype(int8)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    train_data = Dataset(X_train, label=y_train)
    test_data = Dataset(X_test, label=y_test, reference=train_data)

    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": 0.1,
        "num_leaves": 31,
        "verbose": -1,
        # "scale_pos_weight": len(y_train[y_train == 0]) / len(y_train[y_train == 1]),
    }

    model = train(
        params,
        train_data,
        num_boost_round=100,
        valid_sets=[test_data],
        # callbacks=[early_stopping(stopping_rounds=1000000)],
    )
    model.save_model("video_model.txt")
    y_pred = model.predict(X_test)
    y_pred_label = (array(y_pred) >= 0.7).astype(int)

    accuracy = accuracy_score(y_test, y_pred_label)
    print(f"Accuracy: {accuracy:.4f}")

    cm = confusion_matrix(y_test, y_pred_label)
    print(cm)

    print(classification_report(y_test, y_pred_label))

    auc = roc_auc_score(y_test, y_pred)  # type: ignore
    print(f"AUC: {auc:.4f}")

    plot_importance(model, importance_type="gain", max_num_features=20)
    pyplot.show()


def save_training_videos_with_data(data_fun: Callable[[Video], dict], filename: str) -> None:

    videos = Video.select().where((Video.duration_seconds > 60) & (Video.origin == Video.Origin.SCRAPED.value))

    logger.info(f"Saving training videos ({videos.count()} total)...")

    d = []
    for i, video in enumerate(videos):
        logger.info(f"Saving video {i + 1}...")
        d.append(data_fun(video))

    df = pd.DataFrame(data=d)
    df.to_csv(filename)
    logger.info("Done!")


def label_and_desc_embedding(video: Video) -> dict:
    return {
        "desc_embedding": VideoDescriptionEmbedding(video).get(),
        "label": video.label,
    }


save_training_videos_with_data(label_and_desc_embedding, "sam_test_video_desc_data.csv")


# process_videos(videos, "training_data.csv")

# @dataclass
# class TrainingChannel:


# Video.select().where(Video )

# ??? ^^^ not sure what this is

# train_model()

# from youtube import OfficialYouTubeService

# res = OfficialYouTubeService.build_from_env(origin=Video.Origin.APP).videos("lowfi beats", max_results=1)
# breakpoint()


# DATA_PATH = "training_data.csv"
# start = perf_counter()
# data = read_csv(DATA_PATH)
# end = perf_counter()
# logger.info(f"Finished loading {DATA_PATH} after {end - start:.6f} seconds.")

# count = 0
# with open("joey_data_with_video_ids.csv", "a") as file:
#     for row in data.itertuples(index=False):
#         for embedding_vec in loads(row.embeddings):  # type: ignore
#             single_comment_row = (
#                 {
#                     "description_len": row.len,
#                     "description_readability_score": row.readability_score,
#                     "description_num_links": row.num_links,
#                     "description_num_ai_keywords": row.num_ai_keywords,
#                     "description_contains_ai_keywords": row.contains_ai_keywords,
#                     "average_comment_len": row.average_len,
#                     "percent_short_comments": row.percent_short,
#                     "percent_duplicate_comments": row.percent_duplicate,
#                     "comments_emoji_density": row.emoji_density,
#                     "comments_percent_unique_words": row.percent_unique_words,
#                     "comments_generic_praise_ratio": row.generic_praise_ratio,
#                     "video_id": row.video_id,
#                 }
#                 | {f"embedding_dim_{i}": num for i, num in enumerate(embedding_vec)}
#                 | {"label": row.label}
#             )
#             if count == 0:
#                 # write headers
#                 file.write(",".join([str(x) for x in single_comment_row.keys()]) + "\n")
#             # Write CSV row for comment embedding
#             file.write(",".join([str(x) for x in single_comment_row.values()]) + "\n")
#             count += 1
#             logger.debug(f"Wrote line {count}.")
