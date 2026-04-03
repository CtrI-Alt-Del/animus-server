from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    petition_document_path: str


class PetitionReplacedEvent(Event[_Payload]):
    name = 'intake/petition.replaced'

    def __init__(self, petition_document_path: str) -> None:
        payload = _Payload(petition_document_path=petition_document_path)
        super().__init__(PetitionReplacedEvent.name, payload)
