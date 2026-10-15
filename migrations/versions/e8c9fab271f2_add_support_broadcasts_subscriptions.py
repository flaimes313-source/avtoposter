"""add support, broadcasts, subscriptions

Revision ID: <ваш id>
Revises: 870939533199
Create Date: ...

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '<ваш id>'
down_revision: Union[str, None] = '870939533199'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонки в posts и ad_posts
    op.add_column("posts", sa.Column("button_text", sa.Text()))
    op.add_column("posts", sa.Column("button_url", sa.Text()))
    op.add_column("ad_posts", sa.Column("button_text", sa.Text()))
    op.add_column("ad_posts", sa.Column("button_url", sa.Text()))

    # Поле для weekly-check подписок
    op.add_column("users", sa.Column("last_subscription_check",
                                     sa.DateTime(timezone=True)))

    # Поддержка
    op.create_table(
        "support_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("username", sa.Text()),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("answered", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Настройки бота
    op.create_table(
        "bot_settings",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", sa.Text()),
    )

    # Обязательные каналы (рекламные кампании)
    op.create_table(
        "required_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("chat_id", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text()),
        sa.Column("url", sa.Text()),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Состояние подписки конкретного пользователя
    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger()),
        sa.Column("chat_id", sa.Text()),
        sa.Column("is_subscribed", sa.Integer(), server_default="0"),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "chat_id"),
    )


def downgrade() -> None:
    op.drop_table("user_subscriptions")
    op.drop_table("required_channels")
    op.drop_table("bot_settings")
    op.drop_table("support_messages")

    op.drop_column("users", "last_subscription_check")
    op.drop_column("ad_posts", "button_url")
    op.drop_column("ad_posts", "button_text")
    op.drop_column("posts", "button_url")
    op.drop_column("posts", "button_text")