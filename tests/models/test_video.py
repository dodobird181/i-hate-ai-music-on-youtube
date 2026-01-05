import pytest

from models.channel import Channel
from models.video import Video

VIDEO_DATA = {
    "id": "VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
    "snippet": {
        "title": "Test Video",
        "description": "This is a video",
        "thumbnails": {"medium": {"url": "example.com/image.png"}},
        "channelId": "UCyRbMM2KCivYQHnVi8y8AAw",
        "channelTitle": "Test Channel",
    },
    "statistics": {
        "viewCount": 9000,
        "likeCount": 678,
        "favoriteCount": 12,
        "commentCount": 62,
    },
    "status": {"containsSyntheticMedia": False},
    "liveStreamingDetails": {"foo": "bar"},
}


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
def test_from_data_returns_video(data):
    video = Video.from_data(data)
    expected = Video(
        id="VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
        title="Test Video",
        description="This is a video",
        url=f"https://www.youtube.com/watch?v=VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
        thumbnail_url="example.com/image.png",
        channel=Channel(id="UCyRbMM2KCivYQHnVi8y8AAw", title="Test Channel"),
        stats=Video.Statistics(views=9000, likes=678, favorites=12, comments=62),
        is_livestream=True,
        contains_synthetic_media=False,
    )
    assert video == expected


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
