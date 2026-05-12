from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.entities.judge_analysis_status import JudgeAnalysisStatus
from animus.core.intake.domain.entities.lawyer_analysis_status import LawyerAnalysisStatus
from animus.core.intake.domain.errors import AnalysisNotFoundError, AnalysisDocumentNotFoundError
from animus.core.intake.domain.events import CaseSummaryRequestedEvent
from animus.core.intake.interfaces import AnalysisDocumentsRepository, AnalisysesRepository
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class RequestCaseSummaryUseCase:
    def __init__(
        self,
        analysis_documents_repository: AnalysisDocumentsRepository,
        analisyses_repository: AnalisysesRepository,
        broker: Broker,
    ) -> None:
        self._analysis_documents_repository = analysis_documents_repository
        self._analisyses_repository = analisyses_repository
        self._broker = broker

    def execute(self, analysis_id: str) -> None:
        analysis_id_entity = Id.create(analysis_id)

        analysis_document = self._analysis_documents_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if analysis_document is None:
            raise AnalysisDocumentNotFoundError

        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type == AnalysisType.LAWYER:
            analysis.set_status(LawyerAnalysisStatus.ANALYZING_CASE)
        else:
            analysis.set_status(JudgeAnalysisStatus.ANALYZING_CASE)

        self._analisyses_repository.replace(analysis)
        self._broker.publish(CaseSummaryRequestedEvent(analysis_id=analysis_id_entity.value))
