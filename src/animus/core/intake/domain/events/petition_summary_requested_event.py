from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    petition_id: str


class PetitionSummaryRequestedEvent(Event[_Payload]):
    name = 'intake/petition.summary.requested'

    def __init__(self, petition_id: str) -> None:
        payload = _Payload(petition_id=petition_id)
        super().__init__(PetitionSummaryRequestedEvent.name, payload)
