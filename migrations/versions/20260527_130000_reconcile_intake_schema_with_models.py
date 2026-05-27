"""reconcile intake schema with models

Revision ID: 20260527_130000
Revises: 20260527_120000
Create Date: 2026-05-27 13:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260527_130000'
down_revision: str | Sequence[str] | None = '20260527_120000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'petitions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('document_file_path', sa.String(), nullable=False),
        sa.Column('document_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index(
        op.f('ix_petitions_analysis_id'),
        'petitions',
        ['analysis_id'],
        if_not_exists=True,
    )

    op.create_table(
        'petition_summaries',
        sa.Column('petition_id', sa.String(length=26), nullable=False),
        sa.Column('case_summary', sa.Text(), nullable=False),
        sa.Column('legal_issue', sa.Text(), nullable=False),
        sa.Column('central_question', sa.Text(), nullable=False),
        sa.Column('relevant_laws', sa.JSON(), nullable=False),
        sa.Column('key_facts', sa.JSON(), nullable=False),
        sa.Column('search_terms', sa.JSON(), nullable=False),
        sa.Column('type_of_action', sa.Text(), nullable=True),
        sa.Column('secondary_legal_issues', sa.JSON(), nullable=False),
        sa.Column('alternative_questions', sa.JSON(), nullable=False),
        sa.Column('jurisdiction_issue', sa.Text(), nullable=True),
        sa.Column('standing_issue', sa.Text(), nullable=True),
        sa.Column('requested_relief', sa.JSON(), nullable=False),
        sa.Column('procedural_issues', sa.JSON(), nullable=False),
        sa.Column('excluded_or_accessory_topics', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['petition_id'], ['petitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('petition_id'),
        if_not_exists=True,
    )

    op.execute(
        sa.text(
            """
            INSERT INTO petitions (
                id,
                analysis_id,
                uploaded_at,
                document_file_path,
                document_name,
                created_at,
                updated_at
            )
            SELECT
                ad.analysis_id,
                ad.analysis_id,
                ad.uploaded_at,
                ad.document_file_path,
                ad.document_name,
                ad.created_at,
                ad.updated_at
            FROM analysis_documents ad
            WHERE NOT EXISTS (
                SELECT 1
                FROM petitions p
                WHERE p.analysis_id = ad.analysis_id
                  AND p.document_file_path = ad.document_file_path
            )
            ON CONFLICT (id) DO NOTHING
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO petition_summaries (
                petition_id,
                case_summary,
                legal_issue,
                central_question,
                relevant_laws,
                key_facts,
                search_terms,
                type_of_action,
                secondary_legal_issues,
                alternative_questions,
                jurisdiction_issue,
                standing_issue,
                requested_relief,
                procedural_issues,
                excluded_or_accessory_topics,
                created_at,
                updated_at
            )
            SELECT DISTINCT ON (p.id)
                p.id,
                cs.case_summary,
                cs.legal_issue,
                cs.central_question,
                cs.relevant_laws,
                cs.key_facts,
                cs.search_terms,
                cs.type_of_action,
                cs.secondary_legal_issues,
                cs.alternative_questions,
                cs.jurisdiction_issue,
                cs.standing_issue,
                cs.requested_relief,
                cs.procedural_issues,
                cs.excluded_or_accessory_topics,
                cs.created_at,
                cs.updated_at
            FROM case_summaries cs
            INNER JOIN analysis_documents ad ON ad.analysis_id = cs.analysis_id
            INNER JOIN petitions p
                ON p.analysis_id = ad.analysis_id
               AND p.document_file_path = ad.document_file_path
            ORDER BY p.id, cs.updated_at DESC
            ON CONFLICT (petition_id) DO NOTHING
            """
        )
    )

    op.drop_index(
        op.f('ix_analysis_documents_analysis_id'),
        table_name='analysis_documents',
        if_exists=True,
    )
    op.alter_column(
        'analysies_precedent_legal_features',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.alter_column(
        'analysis_precedent_applicability_feedbacks',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.alter_column(
        'analysis_precedent_dataset_rows',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
