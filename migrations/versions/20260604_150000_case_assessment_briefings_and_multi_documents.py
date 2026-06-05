"""case assessment briefings and multi-documents

Revision ID: 20260604_150000
Revises: 20260527_130000
Create Date: 2026-06-04 15:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260604_150000'
down_revision: str | Sequence[str] | None = '20260527_130000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'case_assessment_briefings',
        sa.Column('analysis_id', sa.String(length=26), nullable=False),
        sa.Column('legal_area', sa.String(), nullable=False),
        sa.Column('court_jurisdiction', sa.String(), nullable=False),
        sa.Column('main_claims', sa.Text(), nullable=False),
        sa.Column('intended_thesis', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('analysis_id'),
    )

    op.execute(
        sa.text(
            """
            UPDATE analyses
            SET status = CASE
                WHEN status = 'WAITING_DOCUMENT_UPLOAD' THEN 'WAITING_BRIEFING'
                WHEN status = 'DOCUMENT_UPLOADED' THEN 'BRIEFING_SUBMITTED'
                ELSE status
            END
            WHERE type = 'CASE_ASSESSMENT'
            """
        )
    )

    op.drop_constraint(
        'analysis_documents_pkey',
        'analysis_documents',
        type_='primary',
    )
    op.create_primary_key(
        'analysis_documents_pkey',
        'analysis_documents',
        ['document_file_path'],
    )
    op.create_index(
        op.f('ix_analysis_documents_analysis_id'),
        'analysis_documents',
        ['analysis_id'],
        unique=False,
    )


def downgrade() -> None:
    # Downgrade colapsa multiplos documentos por analise, preservando o upload mais recente.
    op.execute(
        sa.text(
            """
            DELETE FROM analysis_documents
            WHERE document_file_path NOT IN (
                SELECT kept.document_file_path
                FROM (
                    SELECT DISTINCT ON (analysis_id) document_file_path
                    FROM analysis_documents
                    ORDER BY analysis_id, uploaded_at DESC, document_file_path DESC
                ) AS kept
            )
            """
        )
    )

    op.drop_index(
        op.f('ix_analysis_documents_analysis_id'),
        table_name='analysis_documents',
    )
    op.drop_constraint(
        'analysis_documents_pkey',
        'analysis_documents',
        type_='primary',
    )
    op.create_primary_key(
        'analysis_documents_pkey',
        'analysis_documents',
        ['analysis_id'],
    )

    op.execute(
        sa.text(
            """
            UPDATE analyses
            SET status = CASE
                WHEN status = 'WAITING_BRIEFING' THEN 'WAITING_DOCUMENT_UPLOAD'
                WHEN status = 'BRIEFING_SUBMITTED' THEN 'DOCUMENT_UPLOADED'
                ELSE status
            END
            WHERE type = 'CASE_ASSESSMENT'
            """
        )
    )

    op.drop_table('case_assessment_briefings')
