from animus.core.intake.domain.errors import (
    AnalysisDocumentNotFoundError,
    AnalysisNotFoundError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.events import (
    CaseAssessmentCaseSummaryRequestedEvent,
)
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TriggerCaseAssessmentCaseSummarizationUseCase:
    def __init__(
        self,
        analysis_documents_repository: AnalysisDocumentsRepository,
        analyses_repository: AnalysesRepository,
        broker: Broker,
    ) -> None:
        self._analysis_documents_repository = analysis_documents_repository
        self._analyses_repository = analyses_repository
        self._broker = broker

    def execute(self, analysis_id: str) -> None:
        analysis_id_entity = Id.create(analysis_id)

        analysis_document = self._analysis_documents_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if analysis_document is None:
            raise AnalysisDocumentNotFoundError

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_case_analysis.is_false:
            raise InconsistentAnalysisTypeError

        analysis.set_status(CaseAssessmentAnalysisStatus.create_as_analyzing_case())

        event = CaseAssessmentCaseSummaryRequestedEvent(
            analysis_id=analysis_id_entity.value,
        )
        self._analyses_repository.replace(analysis)
        self._broker.publish(event)
