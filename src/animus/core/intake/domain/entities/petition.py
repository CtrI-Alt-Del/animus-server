from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.structures import Datetime, FilePath, Id, Text


@entity
class Petition(Entity):
    analysis_id: Id
    uploaded_at: Datetime
    file_path: FilePath
    name: Text

    @classmethod
    def create(
        cls,
        *,
        petition_id: str | None,
        analysis_id: str,
        uploaded_at: str,
        file_path: str,
        name: str,
    ) -> 'Petition':
        return cls(
            id=Id.create(petition_id),
            analysis_id=Id.create(analysis_id),
            uploaded_at=Datetime.create(uploaded_at),
            file_path=FilePath.create(file_path),
            name=Text.create(name),
        )

    @property
    def dto(self) -> AnalysisDocumentDto:
        return AnalysisDocumentDto(
            analysis_id=self.analysis_id.value,
            uploaded_at=self.uploaded_at.value.isoformat(),
            file_path=self.file_path.value,
            name=self.name.value,
        )
