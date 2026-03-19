from animus.core.shared.domain.decorators import dto


@dto
class PrecedentDto:
    court: str
    number: int
    synthesis: str
    kind: str
    status: str
    title: str
    enunciation: str
    thesis: str
    last_updated_in_pangea_at: str
    id: str | None = None
