import sqlite3
from datetime import datetime, timezone

DB_PATH = "autoposter.db"


def init_db():
    """Создаёт таблицы при первом запуске."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Таблица пользователей (для хранения часового пояса)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            timezone TEXT DEFAULT 'Europe/Moscow'
        )
    """)

    # Таблица для хранения отложенных постов
    # ВАЖНО: scheduled_time хранится в UTC (ISO-формат)
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

    # Таблица для рекламных постов
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

    conn.commit()
    conn.close()


# ==================== USERS ====================

def get_user_timezone(user_id: int) -> str:
    """Возвращает часовой пояс пользователя. Если нет — создаёт запись с дефолтным."""
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
    """Устанавливает часовой пояс пользователя."""
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
    """scheduled_time_utc — ISO-строка в UTC."""
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
    """Посты, время которых пришло (по UTC) и которые ещё не отправлены."""
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
    """Список постов конкретного пользователя (для команды /posts)."""
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