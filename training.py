from dataclasses import asdict
from logging import getLogger
from time import perf_counter

from lightgbm import Dataset, early_stopping, plot_importance, train
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

from feature_extraction import extract
from models import Comment, Video

# videos = Video.select().where((Video.duration_seconds > 60) & (Video.comments >= 50))

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
            | {"embeddings": ",".join(map(str, features.embeddings)), "label": video.label}
        )
        processed_videos.append(video_data)

    df = DataFrame(processed_videos)
    with open(filename, "w") as file:
        file.write(df.to_csv())


def train_model():
    DATA_PATH = "training_data.csv"

    logger.info("Loading training data...")
    start = perf_counter()
    data = read_csv(DATA_PATH)
    end = perf_counter()
    logger.info(f"Finished loading {DATA_PATH} after {end - start:.6f} seconds.")

    X = data.drop(columns=["label", "embeddings", "Unnamed: 0"])

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
        "scale_pos_weight": len(y_train[y_train == 0]) / len(y_train[y_train == 1]),
    }

    model = train(
        params,
        train_data,
        num_boost_round=100,
        valid_sets=[test_data],
        callbacks=[early_stopping(stopping_rounds=50)],
    )
    model.save_model("video_model.txt")
    y_pred = model.predict(X_test)
    y_pred_label = (array(y_pred) >= 0.7).astype(int)

    accuracy = accuracy_score(y_test, y_pred_label)
    print(f"Accuracy: {accuracy:.4f}")

    cm = confusion_matrix(y_test, y_pred_label)
    print(cm)

    print(classification_report(y_test, y_pred_label))

    auc = roc_auc_score(y_test, y_pred_label)
    print(f"AUC: {auc:.4f}")

    plot_importance(model, importance_type="gain", max_num_features=20)
    pyplot.show()


# process_videos(Video.select().where((Video.duration_seconds > 60) & (Video.comments >= 50)), "training_data.csv")
# train_model()
