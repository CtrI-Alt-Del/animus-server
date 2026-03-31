from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    courts: list[str]
    precedent_kinds: list[str]
    limit: int


class AnalysisPrecedentsSearchRequestedEvent(Event[_Payload]):
    name = 'intake/analysis.precedents.search.requested'

    def __init__(
        self,
        analysis_id: str,
        courts: list[str],
        precedent_kinds: list[str],
        limit: int,
    ) -> None:
        payload = _Payload(
            analysis_id=analysis_id,
            courts=courts,
            precedent_kinds=precedent_kinds,
            limit=limit,
        )
        super().__init__(AnalysisPrecedentsSearchRequestedEvent.name, payload)
