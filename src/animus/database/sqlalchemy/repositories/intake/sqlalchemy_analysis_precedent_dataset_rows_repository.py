from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.intake.domain.structures import AnalysisPrecedentDatasetRow
from animus.core.intake.interfaces import AnalysisPrecedentDatasetRowsRepository
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake import AnalysisPrecedentDatasetRowMapper
from animus.database.sqlalchemy.models.intake import AnalysisPrecedentDatasetRowModel


class SqlalchemyAnalysisPrecedentDatasetRowsRepository(
    AnalysisPrecedentDatasetRowsRepository
):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> AnalysisPrecedentDatasetRow | None:
        model = self._sqlalchemy.scalar(
            select(AnalysisPrecedentDatasetRowModel).where(
                AnalysisPrecedentDatasetRowModel.analysis_id == analysis_id.value,
                AnalysisPrecedentDatasetRowModel.precedent_id == precedent_id.value,
            )
        )
        if model is None:
            return None

        return AnalysisPrecedentDatasetRowMapper.to_entity(model)

    def add(self, dataset_row: AnalysisPrecedentDatasetRow) -> None:
        self._sqlalchemy.add(AnalysisPrecedentDatasetRowMapper.to_model(dataset_row))

    def replace(self, dataset_row: AnalysisPrecedentDatasetRow) -> None:
        model = self._sqlalchemy.scalar(
            select(AnalysisPrecedentDatasetRowModel).where(
                AnalysisPrecedentDatasetRowModel.analysis_id
                == dataset_row.analysis_id.value,
                AnalysisPrecedentDatasetRowModel.precedent_id
                == dataset_row.precedent_id.value,
            )
        )
        if model is None:
            return

        identifier_dto = dataset_row.identifier.dto

        model.created_at = dataset_row.created_at.value
        model.applicability_level = dataset_row.applicability_level.dto
        model.is_from_human = dataset_row.is_from_human.value
        model.thesis_similarity_score = dataset_row.thesis_similarity_score.value
        model.enunciation_similarity_score = (
            dataset_row.enunciation_similarity_score.value
        )
        model.total_search_hits = dataset_row.total_search_hits.value
        model.similarity_rank = dataset_row.similarity_rank.value
        model.identifier_court = identifier_dto.court
        model.identifier_kind = identifier_dto.kind
        model.identifier_number = identifier_dto.number
        model.precedent_status = dataset_row.precedent_status.value
        model.last_updated_in_pangea_at = dataset_row.last_updated_in_pangea_at.value
