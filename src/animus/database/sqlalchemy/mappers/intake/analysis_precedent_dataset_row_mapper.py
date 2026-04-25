from animus.core.intake.domain.structures import AnalysisPrecedentDatasetRow
from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_dto import (
    AnalysisPrecedentDatasetDto,
)
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.database.sqlalchemy.models.intake.analysis_precedent_dataset_row_model import (
    AnalysisPrecedentDatasetRowModel,
)


class AnalysisPrecedentDatasetRowMapper:
    @staticmethod
    def to_entity(
        model: AnalysisPrecedentDatasetRowModel,
    ) -> AnalysisPrecedentDatasetRow:
        return AnalysisPrecedentDatasetRow.create(
            AnalysisPrecedentDatasetDto(
                analysis_id=model.analysis_id,
                precedent_id=model.precedent_id,
                created_at=model.created_at.isoformat(),
                applicability_level=model.applicability_level,
                is_from_human=model.is_from_human,
                thesis_similarity_score=model.thesis_similarity_score,
                enunciation_similarity_score=model.enunciation_similarity_score,
                total_search_hits=model.total_search_hits,
                similarity_rank=model.similarity_rank,
                identifier=PrecedentIdentifierDto(
                    court=model.identifier_court,
                    kind=model.identifier_kind,
                    number=model.identifier_number,
                ),
                precedent_status=model.precedent_status,
                last_updated_in_pangea_at=model.last_updated_in_pangea_at.isoformat(),
            )
        )

    @staticmethod
    def to_model(
        dataset_row: AnalysisPrecedentDatasetRow,
    ) -> AnalysisPrecedentDatasetRowModel:
        identifier_dto = dataset_row.identifier.dto

        return AnalysisPrecedentDatasetRowModel(
            analysis_id=dataset_row.analysis_id.value,
            precedent_id=dataset_row.precedent_id.value,
            created_at=dataset_row.created_at.value,
            applicability_level=dataset_row.applicability_level.dto,
            is_from_human=dataset_row.is_from_human.value,
            thesis_similarity_score=dataset_row.thesis_similarity_score.value,
            enunciation_similarity_score=dataset_row.enunciation_similarity_score.value,
            total_search_hits=dataset_row.total_search_hits.value,
            similarity_rank=dataset_row.similarity_rank.value,
            identifier_court=identifier_dto.court,
            identifier_kind=identifier_dto.kind,
            identifier_number=identifier_dto.number,
            precedent_status=dataset_row.precedent_status.value,
            last_updated_in_pangea_at=dataset_row.last_updated_in_pangea_at.value,
        )
