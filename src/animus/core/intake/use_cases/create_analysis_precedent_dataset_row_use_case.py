from animus.core.intake.domain.structures import AnalysisPrecedentDatasetRow
from animus.core.intake.domain.structures.dtos.analysis_precedent_applicability_feedback_dto import (
    AnalysisPrecedentApplicabilityFeedbackDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_dto import (
    AnalysisPrecedentDatasetDto,
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
    ) -> AnalysisPrecedentDatasetDto:
        dataset_row = AnalysisPrecedentDatasetRow.create(
            AnalysisPrecedentDatasetDto(
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
