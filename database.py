import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timezone, timedelta

from config import DATABASE_URL


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)


# ==================== USERS ====================

def get_user_timezone(user_id: int) -> str:
    from config import DEFAULT_TIMEZONE
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT timezone FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO users (user_id, timezone) VALUES (%s, %s)",
            (user_id, DEFAULT_TIMEZONE)
        )
        conn.commit()
        conn.close()
        return DEFAULT_TIMEZONE
    conn.close()
    return row["timezone"]


def set_user_timezone(user_id: int, tz: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, timezone) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET timezone = EXCLUDED.timezone
    """, (user_id, tz))
    conn.commit()
    conn.close()


def get_all_user_ids():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


# ==================== POSTS ====================

def add_post(user_id, channel_id, media_type, media_file_id, text,
             links, emojis, button_text, button_url, scheduled_time_utc):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO posts
            (user_id, channel_id, media_type, media_file_id, text, links, emojis,
             button_text, button_url, scheduled_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, channel_id, media_type, media_file_id, text,
          links, emojis, button_text, button_url, scheduled_time_utc))
    conn.commit()
    conn.close()


def get_pending_posts(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    now_utc = datetime.now(timezone.utc)
    cur.execute("""
        SELECT id, channel_id, media_type, media_file_id, text, links, emojis,
               button_text, button_url
        FROM posts
        WHERE is_sent = 0 AND scheduled_time <= %s
        ORDER BY scheduled_time ASC
        LIMIT %s
    """, (now_utc, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_sent(post_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET is_sent = 1 WHERE id = %s", (post_id,))
    conn.commit()
    conn.close()


def get_user_posts(user_id: int, limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, channel_id, media_type, text, scheduled_time, is_sent
        FROM posts
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT %s
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


# ==================== AD POSTS ====================

def add_ad_post(user_id, media_type, media_file_id, text, links, emojis,
                button_text, button_url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ad_posts
            (user_id, media_type, media_file_id, text, links, emojis,
             button_text, button_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, media_type, media_file_id, text, links, emojis,
          button_text, button_url))
    conn.commit()
    conn.close()


# ==================== USER CHANNELS ====================

def add_user_channel(user_id: int, chat_id: str, title: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_channels (user_id, chat_id, title) VALUES (%s, %s, %s)
        ON CONFLICT (user_id, chat_id) DO UPDATE SET title = EXCLUDED.title
    """, (user_id, str(chat_id), title))
    conn.commit()
    conn.close()


def get_user_channels(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT chat_id, title FROM user_channels
        WHERE user_id = %s
        ORDER BY added_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def remove_user_channel(user_id: int, chat_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM user_channels WHERE user_id = %s AND chat_id = %s
    """, (user_id, str(chat_id)))
    conn.commit()
    conn.close()


# ==================== SUPPORT MESSAGES ====================

def add_support_message(user_id: int, username: str, text: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO support_messages (user_id, username, text)
        VALUES (%s, %s, %s)
    """, (user_id, username, text))
    conn.commit()
    conn.close()


def get_open_support_messages():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, username, text, created_at
        FROM support_messages
        WHERE answered = 0
        ORDER BY id ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_support_message(msg_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, username, text, answered FROM support_messages
        WHERE id = %s
    """, (msg_id,))
    row = cur.fetchone()
    conn.close()
    return row


def mark_support_answered(msg_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE support_messages SET answered = 1 WHERE id = %s", (msg_id,))
    conn.commit()
    conn.close()


# ==================== REQUIRED CHANNELS (рекламные кампании) ====================

def add_required_channel(chat_id: str, title: str, url: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO required_channels (chat_id, title, url)
        VALUES (%s, %s, %s)
        ON CONFLICT (chat_id) DO UPDATE
            SET title = EXCLUDED.title, url = EXCLUDED.url
    """, (str(chat_id), title, url))
    conn.commit()
    conn.close()


def get_required_channels():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, chat_id, title, url
        FROM required_channels
        ORDER BY id ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def remove_required_channel(chat_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM required_channels WHERE chat_id = %s", (str(chat_id),))
    conn.commit()
    conn.close()


# ==================== BOT SETTINGS ====================

def get_setting(key: str, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM bot_settings WHERE key = %s", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bot_settings (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (key, value))
    conn.commit()
    conn.close()


def is_subscription_required() -> bool:
    return get_setting("subscription_required", "0") == "1"


def toggle_subscription_required() -> bool:
    current = is_subscription_required()
    set_setting("subscription_required", "0" if current else "1")
    return not current


# ==================== USER SUBSCRIPTIONS ====================

def get_subscribed_channels(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT chat_id FROM user_subscriptions
        WHERE user_id = %s AND is_subscribed = 1
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return {r["chat_id"] for r in rows}


def set_subscription(user_id: int, chat_id: str, is_subscribed: bool):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_subscriptions (user_id, chat_id, is_subscribed)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, chat_id) DO UPDATE
            SET is_subscribed = EXCLUDED.is_subscribed,
                checked_at = CURRENT_TIMESTAMP
    """, (user_id, str(chat_id), 1 if is_subscribed else 0))
    conn.commit()
    conn.close()


def get_users_for_weekly_check():
    """Пользователи, у которых последняя проверка была больше 7 дней назад (или никогда)."""
    conn = get_connection()
    cur = conn.cursor()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    cur.execute("""
        SELECT user_id FROM users
        WHERE last_subscription_check IS NULL OR last_subscription_check < %s
    """, (week_ago,))
    rows = cur.fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


def update_last_subscription_check(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET last_subscription_check = CURRENT_TIMESTAMP
        WHERE user_id = %s
    """, (user_id,))
    conn.commit()
    conn.close()