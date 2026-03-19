from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class PetitionDto:
    id: str | None = None
    analysis_id: str
    uploaded_at: str
    document: PetitionDocumentDto
