import sqlite3

SCRAPE_DB_PATH = "scrape_db"

with sqlite3.connect(SCRAPE_DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT NOT NULL,
            thumbnail_url TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            channel_title TEXT NOT NULL,
            views INTEGER NOT NULL,
            likes INTEGER NOT NULL,
            favorites INTEGER NOT NULL,
            comments INTEGER NOT NULL,
            is_livestream BOOLEAN NOT NULL,
            contains_synthetic_media BOOLEAN NOT NULL,
        )
        CREATE TABLE IF NOT EXISTS comments (
            video_id TEXT PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT NOT NULL,
            thumbnail_url TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            channel_title TEXT NOT NULL,
            views INTEGER NOT NULL,
            likes INTEGER NOT NULL,
            favorites INTEGER NOT NULL,
            comments INTEGER NOT NULL,
            is_livestream BOOLEAN NOT NULL,
            contains_synthetic_media BOOLEAN NOT NULL,
        )
        """
    )
