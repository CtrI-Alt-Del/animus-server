from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.entities.judge_analysis_status import JudgeAnalysisStatus
from animus.core.intake.domain.entities.lawyer_analysis_status import LawyerAnalysisStatus
from animus.core.intake.domain.events import PetitionReplacedEvent
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import AnalysisDocumentsRepository, AnalisysesRepository
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class CreateAnalysisDocumentUseCase:
    def __init__(
        self,
        analysis_documents_repository: AnalysisDocumentsRepository,
        analisyses_repository: AnalisysesRepository,
        broker: Broker,
    ) -> None:
        self._analysis_documents_repository = analysis_documents_repository
        self._analisyses_repository = analisyses_repository
        self._broker = broker

    def execute(
        self,
        analysis_id: str,
        uploaded_at: str,
        file_path: str,
        name: str,
    ) -> AnalysisDocumentDto:
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        existing_document = self._analysis_documents_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if existing_document is None:
            operation = self._analysis_documents_repository.add
        else:
            self._broker.publish(
                PetitionReplacedEvent(
                    petition_document_path=existing_document.file_path.value,
                )
            )
            operation = self._analysis_documents_repository.replace

        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id_entity.value,
                uploaded_at=uploaded_at,
                file_path=file_path,
                name=name,
            )
        )
        operation(document)

        if analysis.type == AnalysisType.LAWYER:
            analysis.set_status(LawyerAnalysisStatus.DOCUMENT_UPLOADED)
        else:
            analysis.set_status(JudgeAnalysisStatus.DOCUMENT_UPLOADED)
        self._analisyses_repository.replace(analysis)

        return document.dto
