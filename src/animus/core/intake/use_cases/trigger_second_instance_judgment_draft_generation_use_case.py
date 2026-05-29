from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    AnalysisPrecedentsUnavailableError,
    CaseSummaryUnavailableError,
    ChosenAnalysisPrecedentsRequiredError,
    SecondInstanceAnalysisRequiredError,
)
from animus.core.intake.domain.events import (
    SecondInstanceJudgmentDraftGenerationTriggeredEvent,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TriggerSecondInstanceJudgmentDraftGenerationUseCase:
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

        if analysis.type != AnalysisType.create_as_second_instance():
            raise SecondInstanceAnalysisRequiredError

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

        analysis.set_status(
            SecondInstanceAnalysisStatus.create_as_generating_judgment_draft()
        )
        self._analyses_repository.replace(analysis)

        self._broker.publish(
            SecondInstanceJudgmentDraftGenerationTriggeredEvent(
                analysis_id=analysis_id_entity.value,
            )
        )
