"""merge final rank head with legacy head

Revision ID: d40da3f4643d
Revises: 20260426_160000, 2ee630b3a47c
Create Date: 2026-04-26 19:34:40.079293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd40da3f4643d'
down_revision: Union[str, Sequence[str], None] = ('20260426_160000', '2ee630b3a47c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
