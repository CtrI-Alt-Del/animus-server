"""merge cascade fk and analyses branches

Revision ID: 2ee630b3a47c
Revises: 20260404_120000, 4ab74425d1ee
Create Date: 2026-04-13 22:47:23.534577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ee630b3a47c'
down_revision: Union[str, Sequence[str], None] = ('20260404_120000', '4ab74425d1ee')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
