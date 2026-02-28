from logging import getLogger
from time import perf_counter

from numpy import float32
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from src.models import Video

logger = getLogger(__name__)


class Sentence:
    """
    A singleton instance of a sentence transformer
    """

    def __new__(cls, *args, model_name="paraphrase-MiniLM-L3-v2", **kwargs):
        if not hasattr(cls, "_instance"):
            logger.info(f"Initializing sentence transformer {model_name}...")
            start = perf_counter()
            cls._instance = SentenceTransformer(model_name)
            end = perf_counter()
            logger.info(f"Finished initializing {model_name} after {end - start:.6f} seconds.")
        return cls._instance


class VideoDescriptionEmbedding:

    def __init__(self, video: Video):
        self.video = video

    def get(self) -> NDArray[float32]:
        transformer = Sentence(model_name="all-mpnet-base-v2")
        embeddings = transformer.encode([self.video.description], show_progress_bar=False)  # type: ignore
        return embeddings[0]
