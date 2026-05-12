from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.interfaces.analysis_documents_repository import (
    AnalysisDocumentsRepository,
)
from animus.core.shared.domain.structures import FilePath, Id
from animus.database.sqlalchemy.mappers.intake.analysis_document_mapper import (
    AnalysisDocumentMapper,
)
from animus.database.sqlalchemy.models.intake.analysis_document_model import (
    AnalysisDocumentModel,
)


class SqlalchemyAnalysisDocumentsRepository(AnalysisDocumentsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(self, analysis_id: Id) -> AnalysisDocument | None:
        model = self._sqlalchemy.get(AnalysisDocumentModel, analysis_id.value)
        if model is None:
            return None

        return AnalysisDocumentMapper.to_entity(model)

    def find_by_file_path(self, file_path: FilePath) -> AnalysisDocument | None:
        model = self._sqlalchemy.scalar(
            select(AnalysisDocumentModel).where(
                AnalysisDocumentModel.document_file_path == file_path.value
            )
        )
        if model is None:
            return None

        return AnalysisDocumentMapper.to_entity(model)

    def add(self, document: AnalysisDocument) -> None:
        self._sqlalchemy.add(AnalysisDocumentMapper.to_model(document))

    def replace(self, document: AnalysisDocument) -> None:
        model = self._sqlalchemy.get(AnalysisDocumentModel, document.analysis_id.value)
        if model is None:
            self.add(document)
            return

        model.uploaded_at = document.uploaded_at.value
        model.document_file_path = document.file_path.value
        model.document_name = document.name.value

    def remove_by_analysis_id(self, analysis_id: Id) -> None:
        model = self._sqlalchemy.get(AnalysisDocumentModel, analysis_id.value)
        if model is None:
            return

        self._sqlalchemy.delete(model)
