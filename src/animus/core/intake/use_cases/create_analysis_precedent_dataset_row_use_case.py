from animus.core.intake.domain.structures import AnalysisPrecedentDatasetRow
from animus.core.intake.domain.structures.dtos.analysis_precedent_applicability_feedback_dto import (
    AnalysisPrecedentApplicabilityFeedbackDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_dto import (
    AnalysisPrecedentDatasetRowDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.interfaces import AnalysisPrecedentDatasetRowsRepository


class CreateAnalysisPrecedentDatasetRowUseCase:
    def __init__(
        self,
        dataset_rows_repository: AnalysisPrecedentDatasetRowsRepository,
    ) -> None:
        self._dataset_rows_repository = dataset_rows_repository

    def execute(
        self,
        analysis_precedent: AnalysisPrecedentDto,
        feedback: AnalysisPrecedentApplicabilityFeedbackDto,
    ) -> AnalysisPrecedentDatasetRowDto:
        legal_features = analysis_precedent.legal_features

        dataset_row = AnalysisPrecedentDatasetRow.create(
            AnalysisPrecedentDatasetRowDto(
                analysis_id=analysis_precedent.analysis_id,
                precedent_id=feedback.precedent_id,
                created_at=feedback.created_at,
                applicability_level=feedback.applicability_level,
                is_from_human=feedback.is_from_human,
                thesis_similarity_score=analysis_precedent.thesis_similarity_score,
                enunciation_similarity_score=(
                    analysis_precedent.enunciation_similarity_score
                ),
                total_search_hits=analysis_precedent.total_search_hits,
                similarity_rank=analysis_precedent.similarity_rank,
                identifier=analysis_precedent.precedent.identifier,
                precedent_status=analysis_precedent.precedent.status,
                last_updated_in_pangea_at=(
                    analysis_precedent.precedent.last_updated_in_pangea_at
                ),
                central_issue_match=(
                    legal_features.central_issue_match
                    if legal_features is not None
                    else 0
                ),
                structural_issue_match=(
                    legal_features.structural_issue_match
                    if legal_features is not None
                    else 0
                ),
                context_compatibility=(
                    legal_features.context_compatibility
                    if legal_features is not None
                    else 0
                ),
                is_lateral_topic=(
                    legal_features.is_lateral_topic if legal_features is not None else 0
                ),
                is_accessory_topic=(
                    legal_features.is_accessory_topic
                    if legal_features is not None
                    else 0
                ),
            )
        )

        existing_dataset_row = (
            self._dataset_rows_repository.find_by_analysis_id_and_precedent_id(
                analysis_id=dataset_row.analysis_id,
                precedent_id=dataset_row.precedent_id,
            )
        )

        if existing_dataset_row is None:
            self._dataset_rows_repository.add(dataset_row)
        else:
            self._dataset_rows_repository.replace(dataset_row)

        return dataset_row.dto
