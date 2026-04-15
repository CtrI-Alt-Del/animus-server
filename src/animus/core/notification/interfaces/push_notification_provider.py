from typing import Protocol

from animus.core.shared.domain.structures import Id


class PushNotificationProvider(Protocol):
    def send_petition_summary_finished_message(
        self,
        *,
        recipient_id: Id,
        analysis_id: Id,
    ) -> None: ...

    def send_precedents_search_finished_message(
        self,
        *,
        recipient_id: Id,
        analysis_id: Id,
    ) -> None: ...
