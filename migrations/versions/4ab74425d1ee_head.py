"""head

Revision ID: 4ab74425d1ee
Revises: 20260330_120000
Create Date: 2026-04-04 01:23:05.859794

"""

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = '4ab74425d1ee'
down_revision: str | Sequence[str] | None = '20260330_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - no-op since tables already created in other branch."""
    pass


def downgrade() -> None:
    """Downgrade schema - no-op since tables already created in other branch."""
    pass
