import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Оригинальный URL от Bothost (используется psycopg2.connect в database.py)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bothost_db_28ec13f550b0:O9EiVcanQ8TLaMgbdyLJyAlNzrwjhA0NCsqYhh1e6hg@node1.pghost.ru:16219/bothost_db_28ec13f550b0"
)

# Тот же URL, но с явным драйвером для SQLAlchemy/Alembic
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL_SQLALCHEMY = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )
else:
    DATABASE_URL_SQLALCHEMY = DATABASE_URL