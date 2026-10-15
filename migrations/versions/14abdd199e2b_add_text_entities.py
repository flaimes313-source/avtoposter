"""add text_entities

Revision ID: <оставьте как есть>
Revises: <оставьте как есть>
Create Date: <оставьте как есть>

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '<оставьте как есть>'
down_revision: Union[str, None] = '<оставьте как есть>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("text_entities", sa.Text()))
    op.add_column("ad_posts", sa.Column("text_entities", sa.Text()))


def downgrade() -> None:
    op.drop_column("posts", "text_entities")
    op.drop_column("ad_posts", "text_entities")