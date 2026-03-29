from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event
from animus.core.shared.domain.structures.id import Id


@dataclass(frozen=True)
class _Payload:
    analysis_id: Id


class SynthesisGenerationStartedEvent(Event[_Payload]):
    name = "intake/synthesis.generation.started"

    def __init__(self, analysis_id: Id) -> None:
        payload = _Payload(analysis_id=analysis_id)
        super().__init__(SynthesisGenerationStartedEvent.name, payload)
