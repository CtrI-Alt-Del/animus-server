from typing import Protocol

from animus.core.shared.domain.structures import Id


class PushNotificationProvider(Protocol):
    def send_case_summary_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
        analysis_type: str,
    ) -> None: ...

    def send_petition_summary_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
        analysis_type: str,
    ) -> None: ...

    def send_precedents_search_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
        analysis_type: str,
    ) -> None: ...

    def send_petition_draft_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
        analysis_type: str,
    ) -> None: ...

    def send_judgment_draft_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
        analysis_type: str,
    ) -> None: ...
