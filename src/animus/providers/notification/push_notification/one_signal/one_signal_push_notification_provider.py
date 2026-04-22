from animus.core.notification.interfaces import PushNotificationProvider
from animus.core.shared.domain.structures import Id


class OneSignalPushNotificationProvider(PushNotificationProvider):
    def send_petition_summary_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
    ) -> None:
        # TODO: Implement OneSignal push notification delivery logic
        pass

    def send_precedents_search_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
    ) -> None:
        # TODO: Implement OneSignal push notification delivery logic
        pass
