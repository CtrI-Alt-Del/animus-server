"""head

Revision ID: 4ab74425d1ee
Revises: 20260330_120000
Create Date: 2026-04-04 01:23:05.859794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ab74425d1ee'
down_revision: Union[str, Sequence[str], None] = '20260330_120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - no-op since tables already created in other branch."""
    pass


def downgrade() -> None:
    """Downgrade schema - no-op since tables already created in other branch."""
    pass
