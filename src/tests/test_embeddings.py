from pytest import mark

from src.embeddings import VideoDescriptionEmbedding


@mark.use_db
def test_video_description_embedding_returns_expected_dimensions(video_from_data):
    embedding = VideoDescriptionEmbedding(video_from_data).get()
    assert embedding.shape == (768,)
