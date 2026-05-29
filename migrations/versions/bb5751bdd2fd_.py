"""no-op duplicate accounts revision

Revision ID: bb5751bdd2fd
Revises: 20260319_000001
Create Date: 2026-03-24 09:03:35.772981

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'bb5751bdd2fd'
down_revision: str | Sequence[str] | None = '20260319_000001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
