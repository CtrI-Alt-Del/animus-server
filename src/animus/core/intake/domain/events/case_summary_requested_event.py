from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    analysis_id: str


class CaseSummaryRequestedEvent(Event[_Payload]):
    name = 'intake/case_summary.requested'

    def __init__(self, analysis_id: str) -> None:
        payload = _Payload(analysis_id=analysis_id)
        super().__init__(CaseSummaryRequestedEvent.name, payload)
