import sqlite3
from datetime import datetime, timezone

DB_PATH = "autoposter.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            timezone TEXT DEFAULT 'Europe/Moscow'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_id TEXT NOT NULL,
            media_type TEXT,
            media_file_id TEXT,
            text TEXT,
            links TEXT,
            emojis TEXT,
            scheduled_time TEXT,
            is_sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ad_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            media_type TEXT,
            media_file_id TEXT,
            text TEXT,
            links TEXT,
            emojis TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Новое: известные каналы (куда бот был добавлен)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS known_channels (
            chat_id TEXT PRIMARY KEY,
            title TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ==================== USERS ====================

def get_user_timezone(user_id: int) -> str:
    from config import DEFAULT_TIMEZONE
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT timezone FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            "INSERT INTO users (user_id, timezone) VALUES (?, ?)",
            (user_id, DEFAULT_TIMEZONE)
        )
        conn.commit()
        conn.close()
        return DEFAULT_TIMEZONE

    conn.close()
    return row[0]


def set_user_timezone(user_id: int, tz: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, timezone) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET timezone = excluded.timezone
    """, (user_id, tz))
    conn.commit()
    conn.close()


# ==================== POSTS ====================

def add_post(user_id, channel_id, media_type, media_file_id, text,
             links, emojis, scheduled_time_utc):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts
            (user_id, channel_id, media_type, media_file_id, text, links, emojis, scheduled_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, channel_id, media_type, media_file_id, text,
          links, emojis, scheduled_time_utc))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id


def get_pending_posts(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_utc = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        SELECT id, channel_id, media_type, media_file_id, text, links, emojis
        FROM posts
        WHERE is_sent = 0 AND scheduled_time <= ?
        ORDER BY scheduled_time ASC
        LIMIT ?
    """, (now_utc, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_sent(post_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET is_sent = 1 WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()


def get_user_posts(user_id: int, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, channel_id, media_type, text, scheduled_time, is_sent
        FROM posts
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ==================== AD POSTS ====================

def add_ad_post(user_id, media_type, media_file_id, text, links, emojis):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ad_posts (user_id, media_type, media_file_id, text, links, emojis)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, media_type, media_file_id, text, links, emojis))
    conn.commit()
    conn.close()


def get_last_ad_post(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT media_type, media_file_id, text, links, emojis
        FROM ad_posts
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


# ==================== KNOWN CHANNELS ====================

def save_known_channel(chat_id, title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO known_channels (chat_id, title) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title
    """, (str(chat_id), title))
    conn.commit()
    conn.close()


def remove_known_channel(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM known_channels WHERE chat_id = ?", (str(chat_id),))
    conn.commit()
    conn.close()


def get_known_channels():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, title FROM known_channels ORDER BY added_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows