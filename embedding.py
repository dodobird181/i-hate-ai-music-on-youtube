from logging import getLogger
from time import perf_counter

from sentence_transformers import SentenceTransformer

logger = getLogger(__name__)


class Sentence:

    MODEL_NAME = "paraphrase-MiniLM-L3-v2"

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            logger.info(f"Initializing sentence transformer {cls.MODEL_NAME}...")
            start = perf_counter()
            cls._instance = SentenceTransformer(cls.MODEL_NAME)
            end = perf_counter()
            logger.info(f"Finished initializing {cls.MODEL_NAME} after {end - start:.6f} seconds.")
        return cls._instance
