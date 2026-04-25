"""add petition summary extended fields

Revision ID: 20260423_010000
Revises: 20260420_120000
Create Date: 2026-04-23 01:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260423_010000'
down_revision: str | None = '20260420_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'petition_summaries',
        sa.Column('type_of_action', sa.Text(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column(
            'secondary_legal_issues',
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.add_column(
        'petition_summaries',
        sa.Column(
            'alternative_questions',
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('jurisdiction_issue', sa.Text(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('standing_issue', sa.Text(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column(
            'requested_relief',
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.add_column(
        'petition_summaries',
        sa.Column(
            'procedural_issues',
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.add_column(
        'petition_summaries',
        sa.Column(
            'excluded_or_accessory_topics',
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )

    op.alter_column(
        'petition_summaries',
        'secondary_legal_issues',
        server_default=None,
    )
    op.alter_column(
        'petition_summaries',
        'alternative_questions',
        server_default=None,
    )
    op.alter_column(
        'petition_summaries',
        'requested_relief',
        server_default=None,
    )
    op.alter_column(
        'petition_summaries',
        'procedural_issues',
        server_default=None,
    )
    op.alter_column(
        'petition_summaries',
        'excluded_or_accessory_topics',
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column('petition_summaries', 'excluded_or_accessory_topics')
    op.drop_column('petition_summaries', 'procedural_issues')
    op.drop_column('petition_summaries', 'requested_relief')
    op.drop_column('petition_summaries', 'standing_issue')
    op.drop_column('petition_summaries', 'jurisdiction_issue')
    op.drop_column('petition_summaries', 'alternative_questions')
    op.drop_column('petition_summaries', 'secondary_legal_issues')
    op.drop_column('petition_summaries', 'type_of_action')
