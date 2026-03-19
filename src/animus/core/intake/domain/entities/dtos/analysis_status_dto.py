from animus.core.shared.domain.decorators import dto


@dto
class AnalysisStatusDto:
    value: str
    id: str | None = None
