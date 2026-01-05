from datetime import datetime

import pytest

from models import Channel, Video, db_conn

VIDEO_DATA = {
    "id": "VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
    "snippet": {
        "title": "Test Video",
        "description": "This is a video",
        "thumbnails": {"medium": {"url": "example.com/image.png"}},
        "channelId": "UCyRbMM2KCivYQHnVi8y8AAw",
        "channelTitle": "Test Channel",
        "publishedAt": "2025-11-19T08:55:44Z",
    },
    "statistics": {
        "viewCount": 9000,
        "likeCount": 678,
        "favoriteCount": 12,
        "commentCount": 62,
    },
    "status": {"containsSyntheticMedia": False},
    "liveStreamingDetails": {"foo": "bar"},
    "contentDetails": {
        "duration": "PT5M30S",
    },
}


@pytest.fixture
def video_from_data():
    yield Video(
        id="VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
        title="Test Video",
        description="This is a video",
        url=f"https://www.youtube.com/watch?v=VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
        thumbnail_url="example.com/image.png",
        channel=Channel(id="UCyRbMM2KCivYQHnVi8y8AAw", title="Test Channel"),
        stats=Video.Statistics(views=9000, likes=678, favorites=12, comments=62),
        is_livestream=True,
        contains_synthetic_media=False,
        label=Video.Label.UNLABELLED,
        duration_seconds=330,
        published_at=datetime.fromisoformat("2025-11-19T08:55:44+00:00"),
    )


@pytest.mark.parametrize(
    "data",
    [
        # Correct video data should build a video
        (VIDEO_DATA),
        # Flat video id in data is valid
        (VIDEO_DATA | {"id": "VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR"}),
        # Nested videoId in data is valid
        (VIDEO_DATA | {"id": {"videoId": "VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR"}}),
        # Extra arbitrary data should not cause an error
        (VIDEO_DATA | {"foobar": 123}),
    ],
)
def test_from_data_returns_video(data, video_from_data):
    video = Video.from_data(data)
    assert video == video_from_data


@pytest.mark.parametrize(
    "data, errors",
    [
        # Missing id in data
        (VIDEO_DATA | {"id": None}, ["Path id cannot be None!"]),
        # Malformed nested id dictionary in data
        (VIDEO_DATA | {"id": {"foobar": 123}}, ["Could not parse video_id from data!"]),
        # Missing entire sub-dictionary in data
        (
            VIDEO_DATA | {"snippet": {}},
            [
                "Path snippet.title cannot be None!",
                "Path snippet.description cannot be None!",
                "Path snippet.thumbnails.medium.url cannot be None!",
                "Path snippet.channelId cannot be None!",
                "Path snippet.channelTitle cannot be None!",
                "Path snippet.publishedAt cannot be None!",
            ],
        ),
        # Missing partial sub-dictionary in data
        (
            VIDEO_DATA
            | {
                "snippet": {
                    "title": "Test Video",
                    "description": "This is a video",
                    "thumbnails": {"medium": {"url": None}},
                    "channelId": "UCyRbMM2KCivYQHnVi8y8AAw",
                    "channelTitle": "Test Channel",
                    "publishedAt": "2025-11-19T08:55:44Z",
                },
            },
            ["Path snippet.thumbnails.medium.url cannot be None!"],
        ),
    ],
)
def test_from_data_raises(data: dict, errors: str):
    try:
        Video.from_data(data)
        pytest.fail("Should not be able to make a video with bad data.")
    except Video.ParseError as e:
        assert errors == e.errors


@pytest.mark.use_db
def test_save(video_from_data):
    assert Video.count() == 0
    video_from_data.save()

    # saving increments count in database
    assert Video.count() == 1

    with db_conn() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT video_id FROM videos WHERE video_id = ?", (video_from_data.id,))
        video_row = cursor.fetchone()

        # Video has the correct id in the database
        assert video_row["video_id"] == video_from_data.id

    # saving again with the same id doesn't create another video
    video_from_data.save()
    assert Video.count() == 1


@pytest.mark.use_db
def test_from_db(video_from_data):

    # Can retrieve saved video from database
    video_from_data.save()
    from_db = Video.from_db(video_from_data.id)
    assert from_db == video_from_data

    # Raise error when model is missing
    try:
        Video.from_db("FAKE_ID")
        pytest.fail("The video should not exist.")
    except Video.DoesNotExist as e:
        pass
