import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self, db_path: str = "filter_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_filters (
                    video_id TEXT PRIMARY KEY,
                    humanity_score INTEGER NOT NULL,
                    is_human BOOLEAN NOT NULL,
                    checked_at TIMESTAMP NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_checked_at
                ON video_filters(checked_at)
            """)
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def get_cached_result(self, video_id: str) -> Optional[tuple[int, bool]]:
        """
        Get cached filtering result for a video.
        Returns: (humanity_score, is_human) or None if not cached
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT humanity_score, is_human
                    FROM video_filters
                    WHERE video_id = ?
                    """,
                    (video_id,),
                )
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Cache hit for video {video_id}: score={result[0]}, is_human={result[1]}")
                    return (result[0], bool(result[1]))
                logger.debug(f"Cache miss for video {video_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting cached result for {video_id}: {e}")
            return None

    def cache_result(self, video_id: str, humanity_score: int, is_human: bool):
        """
        Cache a filtering result for a video.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO video_filters
                    (video_id, humanity_score, is_human, checked_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (video_id, humanity_score, is_human, datetime.now()),
                )
                conn.commit()
                logger.debug(f"Cached result for video {video_id}: score={humanity_score}, is_human={is_human}")
        except Exception as e:
            logger.error(f"Error caching result for {video_id}: {e}")

    def clear_cache(self):
        """Clear all cached results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM video_filters")
                conn.commit()
                logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_cache_stats(self) -> dict:
        """Get statistics about the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM video_filters")
                total = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM video_filters WHERE is_human = 1")
                human_count = cursor.fetchone()[0]

                return {
                    "total_cached": total,
                    "human_videos": human_count,
                    "ai_videos": total - human_count,
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"total_cached": 0, "human_videos": 0, "ai_videos": 0}
