import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Строка подключения к PostgreSQL от Bothost.
# Bothost обычно сам подставляет DATABASE_URL, но на всякий случай оставляем fallback.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bothost_db_28ec13f550b0:O9EiVcanQ8TLaMgbdyLJyAlNzrwjhA0NCsqYhh1e6hg@node1.pghost.ru:16219/bothost_db_28ec13f550b0"
)