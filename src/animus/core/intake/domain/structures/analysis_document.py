from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Datetime, FilePath, Id, Text


@structure
class AnalysisDocument(Structure):
    analysis_id: Id
    uploaded_at: Datetime
    file_path: FilePath
    name: Text

    @classmethod
    def create(cls, dto: AnalysisDocumentDto) -> 'AnalysisDocument':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            uploaded_at=Datetime.create(dto.uploaded_at),
            file_path=FilePath.create(dto.file_path),
            name=Text.create(dto.name),
        )

    @property
    def dto(self) -> AnalysisDocumentDto:
        return AnalysisDocumentDto(
            analysis_id=self.analysis_id.value,
            uploaded_at=self.uploaded_at.value.isoformat(),
            file_path=self.file_path.value,
            name=self.name.value,
        )
