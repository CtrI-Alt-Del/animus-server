"""migrate legal features to new schema

Revision ID: 20260426_120000
Revises: 20260425_235000
Create Date: 2026-04-26 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260426_120000'
down_revision: str | None = '20260425_235000'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_new_legal_feature_columns(table_name: str) -> None:
    op.add_column(
        table_name,
        sa.Column('central_issue_match', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        table_name,
        sa.Column(
            'structural_issue_match',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            'context_compatibility',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            'subject_regime_compatibility',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            'requested_relief_relevance',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column('is_lateral_topic', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        table_name,
        sa.Column('is_accessory_topic', sa.Integer(), nullable=False, server_default='0'),
    )


def _drop_new_legal_feature_columns(table_name: str) -> None:
    op.drop_column(table_name, 'is_accessory_topic')
    op.drop_column(table_name, 'is_lateral_topic')
    op.drop_column(table_name, 'requested_relief_relevance')
    op.drop_column(table_name, 'subject_regime_compatibility')
    op.drop_column(table_name, 'context_compatibility')
    op.drop_column(table_name, 'structural_issue_match')
    op.drop_column(table_name, 'central_issue_match')


def _drop_old_legal_feature_columns(table_name: str) -> None:
    op.drop_column(table_name, 'standing_match')
    op.drop_column(table_name, 'jurisdiction_match')
    op.drop_column(table_name, 'has_accessory_topic_overlap')
    op.drop_column(table_name, 'has_specialization_mismatch')
    op.drop_column(table_name, 'has_regime_mismatch')
    op.drop_column(table_name, 'requested_relief_overlap_count')
    op.drop_column(table_name, 'type_of_action_match')
    op.drop_column(table_name, 'same_decree_count')
    op.drop_column(table_name, 'same_law_count')


def _add_old_legal_feature_columns(table_name: str) -> None:
    op.add_column(
        table_name,
        sa.Column('same_law_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        table_name,
        sa.Column('same_decree_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        table_name,
        sa.Column('type_of_action_match', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        table_name,
        sa.Column(
            'requested_relief_overlap_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            'has_regime_mismatch',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            'has_specialization_mismatch',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column(
            'has_accessory_topic_overlap',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        table_name,
        sa.Column('jurisdiction_match', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        table_name,
        sa.Column('standing_match', sa.Integer(), nullable=False, server_default='0'),
    )


def _clear_defaults(table_name: str, columns: list[str]) -> None:
    for column in columns:
        op.alter_column(table_name, column, server_default=None)


def upgrade() -> None:
    _add_new_legal_feature_columns('analysies_precedent_legal_features')
    _add_new_legal_feature_columns('analysis_precedent_dataset_rows')

    op.execute(
        '''
        UPDATE analysies_precedent_legal_features
        SET
            central_issue_match = CASE
                WHEN same_law_count > 0 OR standing_match = 1 THEN 1
                ELSE 0
            END,
            structural_issue_match = type_of_action_match,
            context_compatibility = CASE
                WHEN same_law_count > 0
                    OR same_decree_count > 0
                    OR jurisdiction_match = 1
                    OR standing_match = 1
                THEN 1
                ELSE 0
            END,
            subject_regime_compatibility = CASE
                WHEN has_regime_mismatch = 0 THEN 1
                ELSE 0
            END,
            requested_relief_relevance = requested_relief_overlap_count,
            is_lateral_topic = has_specialization_mismatch,
            is_accessory_topic = has_accessory_topic_overlap
        '''
    )
    op.execute(
        '''
        UPDATE analysis_precedent_dataset_rows
        SET
            central_issue_match = CASE
                WHEN same_law_count > 0 OR standing_match = 1 THEN 1
                ELSE 0
            END,
            structural_issue_match = type_of_action_match,
            context_compatibility = CASE
                WHEN same_law_count > 0
                    OR same_decree_count > 0
                    OR jurisdiction_match = 1
                    OR standing_match = 1
                THEN 1
                ELSE 0
            END,
            subject_regime_compatibility = CASE
                WHEN has_regime_mismatch = 0 THEN 1
                ELSE 0
            END,
            requested_relief_relevance = requested_relief_overlap_count,
            is_lateral_topic = has_specialization_mismatch,
            is_accessory_topic = has_accessory_topic_overlap
        '''
    )

    _drop_old_legal_feature_columns('analysies_precedent_legal_features')
    _drop_old_legal_feature_columns('analysis_precedent_dataset_rows')

    _clear_defaults(
        'analysies_precedent_legal_features',
        [
            'central_issue_match',
            'structural_issue_match',
            'context_compatibility',
            'subject_regime_compatibility',
            'requested_relief_relevance',
            'is_lateral_topic',
            'is_accessory_topic',
        ],
    )
    _clear_defaults(
        'analysis_precedent_dataset_rows',
        [
            'central_issue_match',
            'structural_issue_match',
            'context_compatibility',
            'subject_regime_compatibility',
            'requested_relief_relevance',
            'is_lateral_topic',
            'is_accessory_topic',
        ],
    )


def downgrade() -> None:
    _add_old_legal_feature_columns('analysies_precedent_legal_features')
    _add_old_legal_feature_columns('analysis_precedent_dataset_rows')

    op.execute(
        '''
        UPDATE analysies_precedent_legal_features
        SET
            same_law_count = central_issue_match,
            same_decree_count = 0,
            type_of_action_match = structural_issue_match,
            requested_relief_overlap_count = requested_relief_relevance,
            has_regime_mismatch = CASE
                WHEN subject_regime_compatibility = 1 THEN 0
                ELSE 1
            END,
            has_specialization_mismatch = is_lateral_topic,
            has_accessory_topic_overlap = is_accessory_topic,
            jurisdiction_match = context_compatibility,
            standing_match = central_issue_match
        '''
    )
    op.execute(
        '''
        UPDATE analysis_precedent_dataset_rows
        SET
            same_law_count = central_issue_match,
            same_decree_count = 0,
            type_of_action_match = structural_issue_match,
            requested_relief_overlap_count = requested_relief_relevance,
            has_regime_mismatch = CASE
                WHEN subject_regime_compatibility = 1 THEN 0
                ELSE 1
            END,
            has_specialization_mismatch = is_lateral_topic,
            has_accessory_topic_overlap = is_accessory_topic,
            jurisdiction_match = context_compatibility,
            standing_match = central_issue_match
        '''
    )

    _drop_new_legal_feature_columns('analysies_precedent_legal_features')
    _drop_new_legal_feature_columns('analysis_precedent_dataset_rows')

    _clear_defaults(
        'analysies_precedent_legal_features',
        [
            'same_law_count',
            'same_decree_count',
            'type_of_action_match',
            'requested_relief_overlap_count',
            'has_regime_mismatch',
            'has_specialization_mismatch',
            'has_accessory_topic_overlap',
            'jurisdiction_match',
            'standing_match',
        ],
    )
    _clear_defaults(
        'analysis_precedent_dataset_rows',
        [
            'same_law_count',
            'same_decree_count',
            'type_of_action_match',
            'requested_relief_overlap_count',
            'has_regime_mismatch',
            'has_specialization_mismatch',
            'has_accessory_topic_overlap',
            'jurisdiction_match',
            'standing_match',
        ],
    )
