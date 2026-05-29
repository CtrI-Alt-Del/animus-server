from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    account_id: str
    analysis_type: str


class PetitionDraftGenerationFinishedEvent(Event[_Payload]):
    name = 'intake/petition_draft.generation.finished'

    def __init__(
        self,
        analysis_id: str,
        account_id: str,
        analysis_type: str,
    ) -> None:
        payload = _Payload(
            analysis_id=analysis_id,
            account_id=account_id,
            analysis_type=analysis_type,
        )
        super().__init__(PetitionDraftGenerationFinishedEvent.name, payload)
