"""drop unused legal features columns

Revision ID: 20260426_130000
Revises: 20260426_120000
Create Date: 2026-04-26 13:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260426_130000'
down_revision: str | None = '20260426_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column('analysies_precedent_legal_features', 'requested_relief_relevance')
    op.drop_column('analysies_precedent_legal_features', 'subject_regime_compatibility')

    op.drop_column('analysis_precedent_dataset_rows', 'requested_relief_relevance')
    op.drop_column('analysis_precedent_dataset_rows', 'subject_regime_compatibility')


def downgrade() -> None:
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column(
            'subject_regime_compatibility',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column(
            'requested_relief_relevance',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )

    op.add_column(
        'analysies_precedent_legal_features',
        sa.Column(
            'subject_regime_compatibility',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'analysies_precedent_legal_features',
        sa.Column(
            'requested_relief_relevance',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )

    op.alter_column(
        'analysis_precedent_dataset_rows',
        'subject_regime_compatibility',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'requested_relief_relevance',
        server_default=None,
    )
    op.alter_column(
        'analysies_precedent_legal_features',
        'subject_regime_compatibility',
        server_default=None,
    )
    op.alter_column(
        'analysies_precedent_legal_features',
        'requested_relief_relevance',
        server_default=None,
    )
