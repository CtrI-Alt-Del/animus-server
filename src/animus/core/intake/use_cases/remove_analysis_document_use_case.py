from animus.core.intake.domain.events import AnalysisDocumentRemovedEvent
from animus.core.intake.domain.errors import (
    AnalysisDocumentNotFoundError,
    AnalysisNotFoundError,
)
from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
)
from animus.core.shared.domain.structures import FilePath, Id
from animus.core.shared.interfaces import Broker


class RemoveAnalysisDocumentUseCase:
    def __init__(
        self,
        analysis_documents_repository: AnalysisDocumentsRepository,
        analyses_repository: AnalysesRepository,
        broker: Broker,
    ) -> None:
        self._analysis_documents_repository = analysis_documents_repository
        self._analyses_repository = analyses_repository
        self._broker = broker

    def execute(self, analysis_id: str, file_path: str) -> None:
        analysis_id_entity = Id.create(analysis_id)
        file_path_entity = FilePath.create(file_path)

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        analysis_document = self._analysis_documents_repository.find_by_file_path(
            file_path_entity
        )
        if analysis_document is None:
            raise AnalysisDocumentNotFoundError

        if analysis_document.analysis_id != analysis_id_entity:
            raise AnalysisDocumentNotFoundError

        self._analysis_documents_repository.remove_by_file_path(file_path_entity)
        self._broker.publish(
            AnalysisDocumentRemovedEvent(
                analysis_document_path=analysis_document.file_path.value,
            )
        )

        if analysis.type.is_case_analysis.is_true:
            return

        if analysis.type.is_first_instance.is_true:
            analysis.set_status(
                FirstInstanceAnalysisStatus.create_as_waiting_document_upload()
            )
        elif analysis.type.is_second_instance.is_true:
            analysis.set_status(
                SecondInstanceAnalysisStatus.create_as_waiting_document_upload()
            )

        self._analyses_repository.replace(analysis)
