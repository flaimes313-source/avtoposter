import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timezone

from config import DATABASE_URL


def get_connection():
    """Создаёт подключение к PostgreSQL."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)


def init_db():
    """Создаёт таблицы при первом запуске, если их нет.
    (При использовании Alembic эта функция становится необязательной, но оставим для надёжности)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            timezone TEXT DEFAULT 'Europe/Moscow'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            channel_id TEXT NOT NULL,
            media_type TEXT,
            media_file_id TEXT,
            text TEXT,
            links TEXT,
            emojis TEXT,
            scheduled_time TIMESTAMP WITH TIME ZONE,
            is_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ad_posts (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            media_type TEXT,
            media_file_id TEXT,
            text TEXT,
            links TEXT,
            emojis TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_channels (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            chat_id TEXT,
            title TEXT,
            added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, chat_id)
        )
    """)

    conn.commit()
    conn.close()


# ==================== USERS ====================

def get_user_timezone(user_id: int) -> str:
    from config import DEFAULT_TIMEZONE
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timezone FROM users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            "INSERT INTO users (user_id, timezone) VALUES (%s, %s)",
            (user_id, DEFAULT_TIMEZONE)
        )
        conn.commit()
        conn.close()
        return DEFAULT_TIMEZONE

    conn.close()
    return row[0]


def set_user_timezone(user_id: int, tz: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, timezone) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET timezone = EXCLUDED.timezone
    """, (user_id, tz))
    conn.commit()
    conn.close()


# ==================== POSTS ====================

def add_post(user_id, channel_id, media_type, media_file_id, text,
             links, emojis, scheduled_time_utc):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts
            (user_id, channel_id, media_type, media_file_id, text, links, emojis, scheduled_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, channel_id, media_type, media_file_id, text,
          links, emojis, scheduled_time_utc))
    conn.commit()
    post_id = cursor.fetchone()
    conn.close()
    return post_id


def get_pending_posts(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    now_utc = datetime.now(timezone.utc)
    cursor.execute("""
        SELECT id, channel_id, media_type, media_file_id, text, links, emojis
        FROM posts
        WHERE is_sent = 0 AND scheduled_time <= %s
        ORDER BY scheduled_time ASC
        LIMIT %s
    """, (now_utc, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_sent(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET is_sent = 1 WHERE id = %s", (post_id,))
    conn.commit()
    conn.close()


def get_user_posts(user_id: int, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, channel_id, media_type, text, scheduled_time, is_sent
        FROM posts
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT %s
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ==================== AD POSTS ====================

def add_ad_post(user_id, media_type, media_file_id, text, links, emojis):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ad_posts (user_id, media_type, media_file_id, text, links, emojis)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, media_type, media_file_id, text, links, emojis))
    conn.commit()
    conn.close()


def get_last_ad_post(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT media_type, media_file_id, text, links, emojis
        FROM ad_posts
        WHERE user_id = %s
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


# ==================== USER CHANNELS ====================

def add_user_channel(user_id: int, chat_id: str, title: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_channels (user_id, chat_id, title) VALUES (%s, %s, %s)
        ON CONFLICT (user_id, chat_id) DO UPDATE SET title = EXCLUDED.title
    """, (user_id, str(chat_id), title))
    conn.commit()
    conn.close()


def get_user_channels(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT chat_id, title FROM user_channels
        WHERE user_id = %s
        ORDER BY added_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def remove_user_channel(user_id: int, chat_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM user_channels WHERE user_id = %s AND chat_id = %s
    """, (user_id, str(chat_id)))
    conn.commit()
    conn.close()