"""add legal features columns to analysis precedent dataset rows

Revision ID: 20260425_235000
Revises: 20260425_180000
Create Date: 2026-04-25 23:50:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260425_235000'
down_revision: str | None = '20260425_180000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column('same_law_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column('same_decree_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column('type_of_action_match', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column(
            'requested_relief_overlap_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column(
            'has_regime_mismatch',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column(
            'has_specialization_mismatch',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column(
            'has_accessory_topic_overlap',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column('jurisdiction_match', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'analysis_precedent_dataset_rows',
        sa.Column('standing_match', sa.Integer(), nullable=False, server_default='0'),
    )

    op.alter_column(
        'analysis_precedent_dataset_rows',
        'same_law_count',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'same_decree_count',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'type_of_action_match',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'requested_relief_overlap_count',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'has_regime_mismatch',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'has_specialization_mismatch',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'has_accessory_topic_overlap',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'jurisdiction_match',
        server_default=None,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'standing_match',
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column('analysis_precedent_dataset_rows', 'standing_match')
    op.drop_column('analysis_precedent_dataset_rows', 'jurisdiction_match')
    op.drop_column('analysis_precedent_dataset_rows', 'has_accessory_topic_overlap')
    op.drop_column('analysis_precedent_dataset_rows', 'has_specialization_mismatch')
    op.drop_column('analysis_precedent_dataset_rows', 'has_regime_mismatch')
    op.drop_column('analysis_precedent_dataset_rows', 'requested_relief_overlap_count')
    op.drop_column('analysis_precedent_dataset_rows', 'type_of_action_match')
    op.drop_column('analysis_precedent_dataset_rows', 'same_decree_count')
    op.drop_column('analysis_precedent_dataset_rows', 'same_law_count')
