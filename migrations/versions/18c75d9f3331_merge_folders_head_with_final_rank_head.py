"""merge folders head with final rank head

Revision ID: 18c75d9f3331
Revises: 20260420_120001, d40da3f4643d
Create Date: 2026-05-03 14:24:02.407095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18c75d9f3331'
down_revision: Union[str, Sequence[str], None] = ('20260420_120001', 'd40da3f4643d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
