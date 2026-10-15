"""initial schema

Revision ID: 870939533199
Revises: 
Create Date: 2026-10-15 20:27:37.530870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '870939533199'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Таблица пользователей (часовой пояс)
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("timezone", sa.Text(), server_default="Europe/Moscow"),
    )

    # Таблица отложенных постов
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("channel_id", sa.Text(), nullable=False),
        sa.Column("media_type", sa.Text()),
        sa.Column("media_file_id", sa.Text()),
        sa.Column("text", sa.Text()),
        sa.Column("links", sa.Text()),
        sa.Column("emojis", sa.Text()),
        sa.Column("scheduled_time", sa.DateTime(timezone=True)),
        sa.Column("is_sent", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Таблица рекламных постов
    op.create_table(
        "ad_posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("media_type", sa.Text()),
        sa.Column("media_file_id", sa.Text()),
        sa.Column("text", sa.Text()),
        sa.Column("links", sa.Text()),
        sa.Column("emojis", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Таблица каналов пользователя
    op.create_table(
        "user_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("chat_id", sa.Text()),
        sa.Column("title", sa.Text()),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "chat_id"),
    )


def downgrade() -> None:
    op.drop_table("user_channels")
    op.drop_table("ad_posts")
    op.drop_table("posts")
    op.drop_table("users")