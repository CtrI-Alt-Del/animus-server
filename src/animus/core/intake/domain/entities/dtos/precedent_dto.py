from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class PrecedentDto:
    identifier: PrecedentIdentifierDto
    status: str
    enunciation: str
    thesis: str
    last_updated_in_pangea_at: str
    id: str | None = None
