"""add expeditions notes

Revision ID: ce5173e00b5c
Revises: 4c5d922cd5b3
Create Date: 2026-10-28 12:40:07.920664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce5173e00b5c'
down_revision: Union[str, Sequence[str], None] = '4c5d922cd5b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем необязательный столбец для заметок об экспедиции.
    op.add_column(
        "expeditions",
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # При откате удаляем добавленный столбец.
    op.drop_column("expeditions", "notes")
