"""update petition summaries structure

Revision ID: 20260330_120000
Revises: 20260328_150000
Create Date: 2026-03-30 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260330_120000'
down_revision: str | None = '20260328_150000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'petition_summaries',
        sa.Column('case_summary', sa.Text(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('legal_issue', sa.Text(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('central_question', sa.Text(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('relevant_laws', sa.JSON(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('key_facts', sa.JSON(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('search_terms', sa.JSON(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE petition_summaries
            SET
                case_summary = content,
                legal_issue = content,
                central_question = content,
                relevant_laws = '[]'::json,
                key_facts = main_points,
                search_terms = '[]'::json
            """
        )
    )

    op.alter_column('petition_summaries', 'case_summary', nullable=False)
    op.alter_column('petition_summaries', 'legal_issue', nullable=False)
    op.alter_column('petition_summaries', 'central_question', nullable=False)
    op.alter_column('petition_summaries', 'relevant_laws', nullable=False)
    op.alter_column('petition_summaries', 'key_facts', nullable=False)
    op.alter_column('petition_summaries', 'search_terms', nullable=False)

    op.drop_column('petition_summaries', 'main_points')
    op.drop_column('petition_summaries', 'content')


def downgrade() -> None:
    op.add_column(
        'petition_summaries',
        sa.Column('content', sa.Text(), nullable=True),
    )
    op.add_column(
        'petition_summaries',
        sa.Column('main_points', sa.JSON(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE petition_summaries
            SET
                content = case_summary,
                main_points = key_facts
            """
        )
    )

    op.alter_column('petition_summaries', 'content', nullable=False)
    op.alter_column('petition_summaries', 'main_points', nullable=False)

    op.drop_column('petition_summaries', 'search_terms')
    op.drop_column('petition_summaries', 'key_facts')
    op.drop_column('petition_summaries', 'relevant_laws')
    op.drop_column('petition_summaries', 'central_question')
    op.drop_column('petition_summaries', 'legal_issue')
    op.drop_column('petition_summaries', 'case_summary')
