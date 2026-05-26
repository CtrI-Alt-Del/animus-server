from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    analysis_id: str


class FistInstanceCaseSummarizationTriggeredEvent(Event[_Payload]):
    name = 'intake/first.instance.case.summary.triggered'

    def __init__(self, analysis_id: str) -> None:
        payload = _Payload(analysis_id=analysis_id)
        super().__init__(FistInstanceCaseSummarizationTriggeredEvent.name, payload)
