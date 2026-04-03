from animus.core.intake.domain.errors import PetitionSummaryUnavailableError
from animus.core.intake.domain.events import AnalysisPrecedentsSearchRequestedEvent
from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFilters,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.interfaces import PetitionSummariesRepository
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class RequestAnalysisPrecedentsSearchUseCase:
    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
        broker: Broker,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository
        self._broker = broker

    def execute(
        self, analysis_id: str, dto: AnalysisPrecedentsSearchFiltersDto
    ) -> None:
        analysis_id_entity = Id.create(analysis_id)
        petition_summary = self._petition_summaries_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )

        if petition_summary is None:
            raise PetitionSummaryUnavailableError

        filters = AnalysisPrecedentsSearchFilters.create(dto)
        normalized_filters_dto = filters.dto

        self._broker.publish(
            AnalysisPrecedentsSearchRequestedEvent(
                analysis_id=analysis_id_entity.value,
                courts=normalized_filters_dto.courts,
                precedent_kinds=normalized_filters_dto.precedent_kinds,
                limit=normalized_filters_dto.limit,
            )
        )
