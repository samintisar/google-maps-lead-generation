"""Enhanced database schema with workflows, scoring, communications, campaigns

Revision ID: ecb6db9f41b1
Revises: 623e856216f4
Create Date: 2025-06-02 03:41:15.447519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ecb6db9f41b1'
down_revision: Union[str, None] = '623e856216f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
