from unittest.mock import MagicMock
from animus.core.notification.use_cases import (
    SendPetitionSummaryFinishedNotificationUseCase,
    SendPrecedentsSearchFinishedNotificationUseCase,
)
from animus.core.shared.domain.structures import Id


class TestNotificationUseCases:
    def test_send_petition_summary_finished_notification_use_case(self) -> None:
        push_notification_provider = MagicMock()
        use_case = SendPetitionSummaryFinishedNotificationUseCase(
            push_notification_provider=push_notification_provider
        )
        account_id = Id.create()
        analysis_id = Id.create()

        use_case.execute(account_id=account_id, analysis_id=analysis_id)

        push_notification_provider.send_petition_summary_finished_message.assert_called_once_with(
            recipient_id=account_id,
            analysis_id=analysis_id,
        )

    def test_send_precedents_search_finished_notification_use_case(self) -> None:
        push_notification_provider = MagicMock()
        use_case = SendPrecedentsSearchFinishedNotificationUseCase(
            push_notification_provider=push_notification_provider
        )
        account_id = Id.create()
        analysis_id = Id.create()

        use_case.execute(account_id=account_id, analysis_id=analysis_id)

        push_notification_provider.send_precedents_search_finished_message.assert_called_once_with(
            recipient_id=account_id,
            analysis_id=analysis_id,
        )
