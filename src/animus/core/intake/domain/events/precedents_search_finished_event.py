from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event
from animus.core.shared.domain.structures.id import Id


@dataclass(frozen=True)
class _Payload:
    analysis_id: Id


class PrecedentsSearchFinishedEvent(Event[_Payload]):
    name = 'intake/precedents_search.finished'

    def __init__(self, analysis_id: Id) -> None:
        payload = _Payload(analysis_id=analysis_id)
        super().__init__(PrecedentsSearchFinishedEvent.name, payload)
