from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    CaseSummaryNotFoundError,
    SecondInstanceDecisionNotFoundError,
)
from animus.core.intake.domain.events import AnalysisPrecedentsSearchTriggeredEvent
from animus.core.intake.domain.structures import AnalysisPrecedentsSearchFilters
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseSummariesRepository,
    SecondInstanceDecisionsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class RequestAnalysisPrecedentsSearchUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        second_instance_decisions_repository: SecondInstanceDecisionsRepository,
        case_summaries_repository: CaseSummariesRepository,
        broker: Broker,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._second_instance_decisions_repository = (
            second_instance_decisions_repository
        )
        self._case_summaries_repository = case_summaries_repository
        self._broker = broker

    def execute(
        self, analysis_id: str, dto: AnalysisPrecedentsSearchFiltersDto
    ) -> None:
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_second_instance.is_true:
            decision = self._second_instance_decisions_repository.find_by_analysis_id(
                analysis_id_entity,
            )
            if decision is None:
                raise SecondInstanceDecisionNotFoundError

        case_summary = self._case_summaries_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )

        if case_summary is None:
            raise CaseSummaryNotFoundError

        filters = AnalysisPrecedentsSearchFilters.create(dto)
        normalized_filters_dto = filters.dto

        self._broker.publish(
            AnalysisPrecedentsSearchTriggeredEvent(
                analysis_id=analysis_id_entity.value,
                courts=normalized_filters_dto.courts,
                precedent_kinds=normalized_filters_dto.precedent_kinds,
                limit=normalized_filters_dto.limit,
            )
        )
