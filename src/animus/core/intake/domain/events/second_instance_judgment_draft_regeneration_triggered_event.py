from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    comments: str


class SecondInstanceJudgmentDraftRegenerationTriggeredEvent(Event[_Payload]):
    name = 'intake/judgment_draft.regeneration.triggered'

    def __init__(self, analysis_id: str, comments: str) -> None:
        payload = _Payload(analysis_id=analysis_id, comments=comments)
        super().__init__(
            SecondInstanceJudgmentDraftRegenerationTriggeredEvent.name,
            payload,
        )
