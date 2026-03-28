from ...structures.precedent_identifier import PrecedentIdentifierDto  # noqa: TID252
from animus.core.shared.domain.decorators import dto


@dto
class PrecedentDto:
    identifier: PrecedentIdentifierDto
    status: str
    enunciation: str
    thesis: str
    last_updated_in_pangea_at: str
    id: str | None = None
