from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    account_id: str


class PetitionSummaryFinishedEvent(Event[_Payload]):
    name = 'intake/petition_summary.finished'

    def __init__(self, analysis_id: str, account_id: str) -> None:
        payload = _Payload(analysis_id=analysis_id, account_id=account_id)
        super().__init__(PetitionSummaryFinishedEvent.name, payload)
