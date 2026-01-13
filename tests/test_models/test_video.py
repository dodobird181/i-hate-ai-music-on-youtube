from pytest import mark

from models import Video
from tests.conftest import VIDEO_DATA


@mark.use_db
def test_save_and_get(video_from_data):
    assert 0 == Video.select().count()
    video_from_data.save(force_insert=True)
    assert 1 == Video.select().count()
    assert Video.get(id=VIDEO_DATA["id"]) == video_from_data
