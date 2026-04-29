from animus.core.notification.interfaces import PushNotificationProvider
from animus.core.shared.domain.structures import Id


class SendPrecedentsSearchFinishedNotificationUseCase:
    def __init__(self, push_notification_provider: PushNotificationProvider) -> None:
        self._push_notification_provider = push_notification_provider

    def execute(self, account_id: Id, analysis_id: Id) -> None:
        self._push_notification_provider.send_precedents_search_finished_message(
            recipient_id=account_id,
            analysis_id=analysis_id,
        )
