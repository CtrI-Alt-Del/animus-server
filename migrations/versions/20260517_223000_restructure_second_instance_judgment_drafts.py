"""restructure second instance judgment drafts

Revision ID: 20260517_223000
Revises: 20260516_143500
Create Date: 2026-05-17 22:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260517_223000'
down_revision: str | Sequence[str] | None = '20260516_143500'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'second_instance_judgment_drafts',
        sa.Column('report', sa.Text(), nullable=False, server_default=''),
    )
    op.add_column(
        'second_instance_judgment_drafts',
        sa.Column('merit_analysis', sa.Text(), nullable=False, server_default=''),
    )
    op.add_column(
        'second_instance_judgment_drafts',
        sa.Column(
            'precedent_adherence_analysis',
            sa.Text(),
            nullable=False,
            server_default='',
        ),
    )
    op.add_column(
        'second_instance_judgment_drafts',
        sa.Column('ruling', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.add_column(
        'second_instance_judgment_drafts',
        sa.Column('preliminary_issues', sa.Text(), nullable=True),
    )
    op.add_column(
        'second_instance_judgment_drafts',
        sa.Column('no_applicable_precedent_notice', sa.Text(), nullable=True),
    )

    op.execute(
        """
        UPDATE second_instance_judgment_drafts
        SET report = content,
            merit_analysis = '',
            precedent_adherence_analysis = '',
            ruling = '[]'::json
        """
    )

    op.alter_column('second_instance_judgment_drafts', 'report', server_default=None)
    op.alter_column(
        'second_instance_judgment_drafts',
        'merit_analysis',
        server_default=None,
    )
    op.alter_column(
        'second_instance_judgment_drafts',
        'precedent_adherence_analysis',
        server_default=None,
    )
    op.alter_column('second_instance_judgment_drafts', 'ruling', server_default=None)

    op.drop_column('second_instance_judgment_drafts', 'content')


def downgrade() -> None:
    op.add_column(
        'second_instance_judgment_drafts',
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
    )

    op.execute(
        """
        UPDATE second_instance_judgment_drafts
        SET content = trim(
            both E'\\n' from concat_ws(
                E'\\n\\n',
                CASE
                    WHEN preliminary_issues IS NOT NULL AND preliminary_issues <> ''
                    THEN concat('PRELIMINARY_ISSUES', E'\\n\\n', preliminary_issues)
                    ELSE NULL
                END,
                CASE
                    WHEN report <> ''
                    THEN concat('REPORT', E'\\n\\n', report)
                    ELSE NULL
                END,
                CASE
                    WHEN merit_analysis <> ''
                    THEN concat('MERIT_ANALYSIS', E'\\n\\n', merit_analysis)
                    ELSE NULL
                END,
                CASE
                    WHEN precedent_adherence_analysis <> ''
                    THEN concat(
                        'PRECEDENT_ADHERENCE_ANALYSIS',
                        E'\\n\\n',
                        precedent_adherence_analysis
                    )
                    ELSE NULL
                END,
                CASE
                    WHEN json_array_length(ruling) > 0
                    THEN concat('RULING', E'\\n\\n', array_to_string(ARRAY(
                        SELECT json_array_elements_text(ruling)
                    ), E'\\n'))
                    ELSE NULL
                END,
                CASE
                    WHEN no_applicable_precedent_notice IS NOT NULL
                         AND no_applicable_precedent_notice <> ''
                    THEN concat(
                        'NO_APPLICABLE_PRECEDENT_NOTICE',
                        E'\\n\\n',
                        no_applicable_precedent_notice
                    )
                    ELSE NULL
                END
            )
        )
        """
    )

    op.alter_column('second_instance_judgment_drafts', 'content', server_default=None)
    op.drop_column('second_instance_judgment_drafts', 'no_applicable_precedent_notice')
    op.drop_column('second_instance_judgment_drafts', 'preliminary_issues')
    op.drop_column('second_instance_judgment_drafts', 'ruling')
    op.drop_column('second_instance_judgment_drafts', 'precedent_adherence_analysis')
    op.drop_column('second_instance_judgment_drafts', 'merit_analysis')
    op.drop_column('second_instance_judgment_drafts', 'report')
