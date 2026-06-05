from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    CaseAssessmentBriefingNotFoundError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.events import (
    CaseAssessmentCaseSummarizationTriggeredEvent,
)
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseAssessmentBriefingsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TriggerCaseAssessmentCaseSummarizationUseCase:
    def __init__(
        self,
        case_assessment_briefings_repository: CaseAssessmentBriefingsRepository,
        analyses_repository: AnalysesRepository,
        broker: Broker,
    ) -> None:
        self._case_assessment_briefings_repository = (
            case_assessment_briefings_repository
        )
        self._analyses_repository = analyses_repository
        self._broker = broker

    def execute(self, analysis_id: str) -> None:
        analysis_id_entity = Id.create(analysis_id)

        briefing = self._case_assessment_briefings_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if briefing is None:
            raise CaseAssessmentBriefingNotFoundError

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_case_analysis.is_false:
            raise InconsistentAnalysisTypeError

        analysis.set_status(CaseAssessmentAnalysisStatus.create_as_analyzing_case())

        event = CaseAssessmentCaseSummarizationTriggeredEvent(
            analysis_id=analysis_id_entity.value,
        )
        self._analyses_repository.replace(analysis)
        self._broker.publish(event)
