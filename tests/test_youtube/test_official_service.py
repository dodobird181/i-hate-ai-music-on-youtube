from pytest import fail, mark

from tests.conftest import VIDEO_DATA
from youtube import OfficialYouTubeService


@mark.parametrize(
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
def test_video_from_data_returns_video(data, video_from_data):
    video = OfficialYouTubeService._video_from_data(VIDEO_DATA)
    assert video == video_from_data


@mark.parametrize(
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
        OfficialYouTubeService._video_from_data(data)
        fail("Should not be able to make a video with bad data.")
    except OfficialYouTubeService.VideoParseError as e:
        assert errors == e.errors
