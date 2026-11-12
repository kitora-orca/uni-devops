"""add places description

Revision ID: 4c5d922cd5b3
Revises:
Create Date: 2026-10-28 11:04:44.969059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c5d922cd5b3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем необязательное описание места.
    # nullable=True позволяет сохранить существующие записи без изменений.
    op.add_column(
        "places",
        sa.Column("description", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # Откатываем миграцию: удаляем добавленный столбец.
    op.drop_column("places", "description")
