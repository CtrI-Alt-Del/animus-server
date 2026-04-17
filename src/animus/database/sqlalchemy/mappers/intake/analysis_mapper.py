from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel


class AnalysisMapper:
    @staticmethod
    def to_entity(model: AnalysisModel) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=model.id,
                name=model.name,
                folder_id=model.folder_id,
                account_id=model.account_id,
                status=model.status,
                is_archived=model.is_archived,
                precedents_search_filters=AnalysisMapper._to_filters_dto(model),
                created_at=model.created_at.isoformat(),
            )
        )

    @staticmethod
    def to_model(entity: Analysis) -> AnalysisModel:
        precedents_search_filters_dto = (
            entity.precedents_search_filters.dto
            if entity.precedents_search_filters is not None
            else None
        )

        return AnalysisModel(
            id=entity.id.value,
            name=entity.name.value,
            folder_id=entity.folder_id.value if entity.folder_id is not None else None,
            account_id=entity.account_id.value,
            status=entity.status.value.value,
            is_archived=entity.is_archived.value,
            precedents_search_courts=(
                list(precedents_search_filters_dto.courts)
                if precedents_search_filters_dto is not None
                else None
            ),
            precedents_search_precedent_kinds=(
                list(precedents_search_filters_dto.precedent_kinds)
                if precedents_search_filters_dto is not None
                else None
            ),
            precedents_search_limit=(
                precedents_search_filters_dto.limit
                if precedents_search_filters_dto is not None
                else None
            ),
            created_at=entity.created_at.value,
        )

    @staticmethod
    def _to_filters_dto(
        model: AnalysisModel,
    ) -> AnalysisPrecedentsSearchFiltersDto | None:
        if (
            model.precedents_search_courts is None
            or model.precedents_search_precedent_kinds is None
            or model.precedents_search_limit is None
        ):
            return None

        return AnalysisPrecedentsSearchFiltersDto(
            courts=list(model.precedents_search_courts),
            precedent_kinds=list(model.precedents_search_precedent_kinds),
            limit=model.precedents_search_limit,
        )
