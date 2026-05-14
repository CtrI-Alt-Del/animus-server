from animus.core.intake.domain.entities.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.entities.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    AnalysisDocumentNotFoundError,
)
from animus.core.intake.domain.events import (
    CaseSummaryRequestedEvent,
    PetitionExtractionRequestedEvent,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalisysesRepository,
)
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

        if analysis.type.uses_case_assessment_or_first_instance_flow():
            analysis.set_status(CaseAssessmentAnalysisStatus.ANALYZING_CASE)
            event = CaseSummaryRequestedEvent(analysis_id=analysis_id_entity.value)
        elif analysis.type == AnalysisType.SECOND_INSTANCE:
            analysis.set_status(SecondInstanceAnalysisStatus.EXTRACTING_PETITION)
            event = PetitionExtractionRequestedEvent(
                analysis_id=analysis_id_entity.value
            )
        else:
            msg = f'Tipo de analise invalido para solicitar resumo: {analysis.type}'
            raise ValueError(msg)

        self._analisyses_repository.replace(analysis)
        self._broker.publish(event)
