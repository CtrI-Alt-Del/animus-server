"""merge analyses and petitions heads

Revision ID: d6394e173b37
Revises: 20260328_110000, dea5b6da2e1a
Create Date: 2026-03-27 11:08:53.810555

"""

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = 'd6394e173b37'
down_revision: str | Sequence[str] | None = ('20260328_110000', 'dea5b6da2e1a')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
