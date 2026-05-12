from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.database.sqlalchemy.models.intake.analysis_document_model import (
    AnalysisDocumentModel,
)


class AnalysisDocumentMapper:
    @staticmethod
    def to_entity(model: AnalysisDocumentModel) -> AnalysisDocument:
        return AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=model.analysis_id,
                uploaded_at=model.uploaded_at.isoformat(),
                file_path=model.document_file_path,
                name=model.document_name,
            )
        )

    @staticmethod
    def to_model(document: AnalysisDocument) -> AnalysisDocumentModel:
        return AnalysisDocumentModel(
            analysis_id=document.analysis_id.value,
            uploaded_at=document.uploaded_at.value,
            document_file_path=document.file_path.value,
            document_name=document.name.value,
        )
