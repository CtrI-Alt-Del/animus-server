"""intake analysis documents, case summaries and drafts

Revision ID: 20260511_120000
Revises: 18c75d9f3331
Create Date: 2026-05-11 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260511_120000'
down_revision: str | None = '18c75d9f3331'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'analyses',
        sa.Column('type', sa.String(length=20), nullable=True),
    )

    op.execute(
        sa.text("UPDATE analyses SET type = 'CASE_ASSESSMENT' WHERE type IS NULL")
    )

    op.execute(
        sa.text(
            """
            UPDATE analyses
            SET status = CASE
                WHEN status = 'WAITING_PETITION' THEN 'WAITING_DOCUMENT_UPLOAD'
                WHEN status = 'PETITION_UPLOADED' THEN 'DOCUMENT_UPLOADED'
                WHEN status = 'ANALYZING_PETITION' THEN 'ANALYZING_CASE'
                WHEN status = 'PETITION_ANALYZED' THEN 'CASE_ANALYZED'
                WHEN status = 'ANALYZING_PRECEDENTS_SIMILARITY' THEN 'SEARCHING_PRECEDENTS'
                WHEN status = 'ANALYZING_PRECEDENTS_APPLICABILITY' THEN 'SEARCHING_PRECEDENTS'
                WHEN status = 'GENERATING_SYNTHESIS' THEN 'GENERATING_PETITION_DRAFT'
                WHEN status = 'WAITING_PRECEDENT_CHOISE' THEN 'DONE'
                WHEN status = 'PRECEDENT_CHOSED' THEN 'DONE'
                WHEN status IS NULL OR status = '' THEN 'WAITING_DOCUMENT_UPLOAD'
                ELSE status
            END
            """
        )
    )

    op.alter_column('analyses', 'type', nullable=False)

    op.create_table(
        'analysis_documents',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('document_file_path', sa.String(), nullable=False),
        sa.Column('document_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('analysis_id'),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO analysis_documents (
                analysis_id,
                uploaded_at,
                document_file_path,
                document_name,
                created_at,
                updated_at
            )
            SELECT DISTINCT ON (p.analysis_id)
                p.analysis_id,
                p.uploaded_at,
                p.document_file_path,
                p.document_name,
                p.created_at,
                p.updated_at
            FROM petitions p
            ORDER BY p.analysis_id, p.uploaded_at DESC, p.id DESC
            """
        )
    )

    op.create_table(
        'case_summaries',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
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
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('analysis_id'),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO case_summaries (
                analysis_id,
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
            SELECT
                p.analysis_id,
                ps.case_summary,
                ps.legal_issue,
                ps.central_question,
                ps.relevant_laws,
                ps.key_facts,
                ps.search_terms,
                ps.type_of_action,
                ps.secondary_legal_issues,
                ps.alternative_questions,
                ps.jurisdiction_issue,
                ps.standing_issue,
                ps.requested_relief,
                ps.procedural_issues,
                ps.excluded_or_accessory_topics,
                ps.created_at,
                ps.updated_at
            FROM petition_summaries ps
            INNER JOIN petitions p ON p.id = ps.petition_id
            INNER JOIN analysis_documents ad ON ad.analysis_id = p.analysis_id
            WHERE ad.document_file_path = p.document_file_path
            """
        )
    )

    op.create_table(
        'petition_drafts',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('analysis_id'),
    )

    op.create_table(
        'judgment_drafts',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('analysis_id'),
    )


def downgrade() -> None:
    op.drop_table('judgment_drafts')
    op.drop_table('petition_drafts')
    op.drop_table('case_summaries')
    op.drop_table('analysis_documents')
    op.drop_column('analyses', 'type')
