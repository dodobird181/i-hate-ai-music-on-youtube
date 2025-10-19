import logging
import sqlite3
from datetime import datetime
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocklist_channels (
                    channel_id TEXT PRIMARY KEY,
                    channel_name TEXT,
                    added_at TIMESTAMP NOT NULL
                )
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

                cursor.execute("SELECT COUNT(*) FROM blocklist_channels")
                blocklist_count = cursor.fetchone()[0]

                return {
                    "total_cached": total,
                    "human_videos": human_count,
                    "ai_videos": total - human_count,
                    "blocklisted_channels": blocklist_count,
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"total_cached": 0, "human_videos": 0, "ai_videos": 0, "blocklisted_channels": 0}

    def load_blocklist_from_file(self, file_path: str = "blocklist_channels.txt"):
        """
        Load blocklisted channels from a file and store in database.
        File format: Lines starting with // are comments, channel IDs on their own lines.
        """
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            channel_entries = []
            current_comment = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("//"):
                    # Extract channel name from comment if available
                    if "(" in line and ")" in line:
                        # Format: // Blocked by context menu (Channel Name) (date)
                        start = line.find("(") + 1
                        end = line.find(")", start)
                        current_comment = line[start:end]
                    else:
                        current_comment = None
                elif line.startswith("UC"):  # YouTube channel IDs start with UC
                    channel_entries.append((line, current_comment, datetime.now()))
                    current_comment = None

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO blocklist_channels
                    (channel_id, channel_name, added_at)
                    VALUES (?, ?, ?)
                    """,
                    channel_entries,
                )
                conn.commit()

            logger.info(f"Loaded {len(channel_entries)} blocklisted channels from {file_path}")
            return len(channel_entries)

        except FileNotFoundError:
            logger.warning(f"Blocklist file not found: {file_path}")
            return 0
        except Exception as e:
            logger.error(f"Error loading blocklist from file: {e}")
            return 0

    def is_channel_blocklisted(self, channel_id: str) -> bool:
        """Check if a channel is blocklisted."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM blocklist_channels WHERE channel_id = ?",
                    (channel_id,),
                )
                result = cursor.fetchone()
                is_blocked = result is not None
                if is_blocked:
                    logger.debug(f"Channel {channel_id} is blocklisted")
                return is_blocked
        except Exception as e:
            logger.error(f"Error checking blocklist for channel {channel_id}: {e}")
            return False

    def add_channel_to_blocklist(self, channel_id: str, channel_name: Optional[str] = None):
        """Add a channel to the blocklist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO blocklist_channels
                    (channel_id, channel_name, added_at)
                    VALUES (?, ?, ?)
                    """,
                    (channel_id, channel_name, datetime.now()),
                )
                conn.commit()
                logger.info(f"Added channel {channel_id} to blocklist")
        except Exception as e:
            logger.error(f"Error adding channel to blocklist: {e}")

    def remove_channel_from_blocklist(self, channel_id: str):
        """Remove a channel from the blocklist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM blocklist_channels WHERE channel_id = ?",
                    (channel_id,),
                )
                conn.commit()
                logger.info(f"Removed channel {channel_id} from blocklist")
        except Exception as e:
            logger.error(f"Error removing channel from blocklist: {e}")
