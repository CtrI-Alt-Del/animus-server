"""restructure petition drafts

Revision ID: 20260522_120000
Revises: 20260517_223000
Create Date: 2026-05-22 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260522_120000'
down_revision: str | Sequence[str] | None = '20260517_223000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'petition_drafts',
        sa.Column('structured_facts', sa.Text(), nullable=False, server_default=''),
    )
    op.add_column(
        'petition_drafts',
        sa.Column('legal_grounds', sa.Text(), nullable=False, server_default=''),
    )
    op.add_column(
        'petition_drafts',
        sa.Column('central_thesis', sa.Text(), nullable=False, server_default=''),
    )
    op.add_column(
        'petition_drafts',
        sa.Column(
            'requests', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")
        ),
    )
    op.add_column(
        'petition_drafts',
        sa.Column(
            'precedent_citations',
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )

    op.execute(
        """
        UPDATE petition_drafts
        SET structured_facts = content,
            legal_grounds = '',
            central_thesis = '',
            requests = '[]'::json,
            precedent_citations = '[]'::json
        """
    )

    op.alter_column('petition_drafts', 'structured_facts', server_default=None)
    op.alter_column('petition_drafts', 'legal_grounds', server_default=None)
    op.alter_column('petition_drafts', 'central_thesis', server_default=None)
    op.alter_column('petition_drafts', 'requests', server_default=None)
    op.alter_column('petition_drafts', 'precedent_citations', server_default=None)

    op.drop_column('petition_drafts', 'content')


def downgrade() -> None:
    op.add_column(
        'petition_drafts',
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
    )

    op.execute(
        """
        UPDATE petition_drafts
        SET content = trim(
            both E'\\n' from concat_ws(
                E'\\n\\n',
                CASE
                    WHEN structured_facts <> ''
                    THEN concat('STRUCTURED_FACTS', E'\\n\\n', structured_facts)
                    ELSE NULL
                END,
                CASE
                    WHEN legal_grounds <> ''
                    THEN concat('LEGAL_GROUNDS', E'\\n\\n', legal_grounds)
                    ELSE NULL
                END,
                CASE
                    WHEN central_thesis <> ''
                    THEN concat('CENTRAL_THESIS', E'\\n\\n', central_thesis)
                    ELSE NULL
                END,
                CASE
                    WHEN json_array_length(requests) > 0
                    THEN concat('REQUESTS', E'\\n\\n', array_to_string(ARRAY(
                        SELECT json_array_elements_text(requests)
                    ), E'\\n'))
                    ELSE NULL
                END,
                CASE
                    WHEN json_array_length(precedent_citations) > 0
                    THEN concat(
                        'PRECEDENT_CITATIONS',
                        E'\\n\\n',
                        array_to_string(ARRAY(
                            SELECT json_array_elements_text(precedent_citations)
                        ), E'\\n')
                    )
                    ELSE NULL
                END
            )
        )
        """
    )

    op.alter_column('petition_drafts', 'content', server_default=None)
    op.drop_column('petition_drafts', 'precedent_citations')
    op.drop_column('petition_drafts', 'requests')
    op.drop_column('petition_drafts', 'central_thesis')
    op.drop_column('petition_drafts', 'legal_grounds')
    op.drop_column('petition_drafts', 'structured_facts')
