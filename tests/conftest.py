from datetime import datetime

from pytest import fixture

from db import reset_test_database


@fixture(autouse=True)
def use_db(request):
    """
    Automatically resets the test database before each test is run. Usage: `@pytest.mark.use_db`.
    """
    if request.node.get_closest_marker("use_db"):
        reset_test_database()
        yield
        reset_test_database()
    else:
        # unmarked tests: do nothing
        yield


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


@fixture
def video_from_data():
    """
    A video model instance that should correspond to the raw `VIDEO_DATA` above.
    """
    from models import Video

    yield Video(
        id="VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
        title="Test Video",
        description="This is a video",
        url=f"https://www.youtube.com/watch?v=VVV5UmJNTTJLQ2l2WVFIblZpOHk4QUF3LncyZzRVV2NHcllR",
        thumbnail_url="example.com/image.png",
        channel_id="UCyRbMM2KCivYQHnVi8y8AAw",
        channel_name="Test Channel",
        likes=678,
        comments=62,
        favorites=12,
        views=9000,
        contains_synthetic_media=False,
        label=Video.Label.UNLABELLED,
        duration_seconds=330,
        published_at=datetime.fromisoformat("2025-11-19T08:55:44+00:00"),
    )
