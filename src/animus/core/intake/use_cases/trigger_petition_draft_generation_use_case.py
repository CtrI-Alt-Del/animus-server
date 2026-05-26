from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    AnalysisPrecedentsUnavailableError,
    CaseSummaryUnavailableError,
    ChosenAnalysisPrecedentsRequiredError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.events import PetitionDraftGenerationTriggeredEvent
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TriggerPetitionDraftGenerationUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        case_summaries_repository: CaseSummariesRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        broker: Broker,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._case_summaries_repository = case_summaries_repository
        self._analysis_precedents_repository = analysis_precedents_repository
        self._broker = broker

    def execute(self, analysis_id: str) -> None:
        analysis_id_entity = Id.create(analysis_id)

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_case_analysis.is_false:
            raise InconsistentAnalysisTypeError

        case_summary = self._case_summaries_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if case_summary is None:
            raise CaseSummaryUnavailableError

        analysis_precedents_response = (
            self._analysis_precedents_repository.find_many_by_analysis_id(
                analysis_id_entity,
            )
        )
        if len(analysis_precedents_response.items) == 0:
            raise AnalysisPrecedentsUnavailableError

        if not any(
            analysis_precedent.is_chosen.is_true
            for analysis_precedent in analysis_precedents_response.items
        ):
            raise ChosenAnalysisPrecedentsRequiredError

        self._broker.publish(
            PetitionDraftGenerationTriggeredEvent(
                analysis_id=analysis_id_entity.value,
            )
        )
