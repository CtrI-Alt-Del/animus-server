"""merge petition drafts and manual precedents heads

Revision ID: 20260527_120000
Revises: 20260522_120000, 4d2d879df9c5
Create Date: 2026-05-27 12:00:00
"""

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = '20260527_120000'
down_revision: str | Sequence[str] | None = (
    '20260522_120000',
    '4d2d879df9c5',
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
