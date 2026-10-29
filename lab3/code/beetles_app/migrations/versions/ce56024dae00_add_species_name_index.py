"""add species name index

Revision ID: ce56024dae00
Revises: ce5173e00b5c
Create Date: 2026-10-28 12:43:36.123434

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ce56024dae00'
down_revision: Union[str, Sequence[str], None] = 'ce5173e00b5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём индекс для ускорения поиска по названию вида жука.
    op.create_index(
        "ix_beetle_species_species_name",
        "beetle_species",
        ["species_name"],
        unique=False,
    )


def downgrade() -> None:
    # При откате удаляем созданный индекс.
    op.drop_index(
        "ix_beetle_species_species_name",
        table_name="beetle_species",
    )
