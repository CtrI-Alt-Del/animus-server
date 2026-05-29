from unittest.mock import MagicMock

from animus.core.notification.use_cases import (
    SendCaseSummaryFinishedNotificationUseCase,
    SendJudgmentDraftFinishedNotificationUseCase,
    SendPetitionDraftFinishedNotificationUseCase,
    SendPetitionSummaryFinishedNotificationUseCase,
    SendPrecedentsSearchFinishedNotificationUseCase,
)
from animus.core.shared.domain.structures import Id


class TestNotificationUseCases:
    def test_send_case_summary_finished_notification_use_case(self) -> None:
        push_notification_provider = MagicMock()
        use_case = SendCaseSummaryFinishedNotificationUseCase(
            push_notification_provider=push_notification_provider
        )
        account_id = Id.create()
        analysis_id = Id.create()
        analysis_type = 'FIRST_INSTANCE'

        use_case.execute(
            account_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

        push_notification_provider.send_case_summary_finished_message.assert_called_once_with(
            recipient_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

    def test_send_petition_summary_finished_notification_use_case(self) -> None:
        push_notification_provider = MagicMock()
        use_case = SendPetitionSummaryFinishedNotificationUseCase(
            push_notification_provider=push_notification_provider
        )
        account_id = Id.create()
        analysis_id = Id.create()
        analysis_type = 'FIRST_INSTANCE'

        use_case.execute(
            account_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

        push_notification_provider.send_petition_summary_finished_message.assert_called_once_with(
            recipient_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

    def test_send_petition_draft_finished_notification_use_case(self) -> None:
        push_notification_provider = MagicMock()
        use_case = SendPetitionDraftFinishedNotificationUseCase(
            push_notification_provider=push_notification_provider
        )
        account_id = Id.create()
        analysis_id = Id.create()
        analysis_type = 'CASE_ASSESSMENT'

        use_case.execute(
            account_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

        push_notification_provider.send_petition_draft_finished_message.assert_called_once_with(
            recipient_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

    def test_send_judgment_draft_finished_notification_use_case(self) -> None:
        push_notification_provider = MagicMock()
        use_case = SendJudgmentDraftFinishedNotificationUseCase(
            push_notification_provider=push_notification_provider
        )
        account_id = Id.create()
        analysis_id = Id.create()
        analysis_type = 'SECOND_INSTANCE'

        use_case.execute(
            account_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

        push_notification_provider.send_second_instance_judgment_draft_finished_message.assert_called_once_with(
            recipient_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

    def test_send_precedents_search_finished_notification_use_case(self) -> None:
        push_notification_provider = MagicMock()
        use_case = SendPrecedentsSearchFinishedNotificationUseCase(
            push_notification_provider=push_notification_provider
        )
        account_id = Id.create()
        analysis_id = Id.create()
        analysis_type = 'FIRST_INSTANCE'

        use_case.execute(
            account_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )

        push_notification_provider.send_precedents_search_finished_message.assert_called_once_with(
            recipient_id=account_id,
            analysis_id=analysis_id,
            analysis_type=analysis_type,
        )
