import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.events import PetitionSummaryFinishedEvent
from animus.core.notification import SendPetitionSummaryFinishedNotificationUseCase
from animus.core.shared.domain.structures import Id
from animus.providers.notification import OneSignalPushNotificationProvider


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    account_id: str


class SendPetitionSummaryFinishedNotificationJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='send-petition-summary-finished-notification',
            trigger=TriggerEvent(
                event=PetitionSummaryFinishedEvent.name,
            ),
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                SendPetitionSummaryFinishedNotificationJob._normalize_payload,
                data,
            )
            payload = _Payload(
                analysis_id=str(normalized_data['analysis_id']),
                account_id=str(normalized_data['account_id']),
            )

            await context.step.run(
                'send_notification',
                lambda payload=payload: (
                    SendPetitionSummaryFinishedNotificationJob._send_notification(
                        payload
                    )
                ),
            )

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {
            'analysis_id': str(data['analysis_id']),
            'account_id': str(data['account_id']),
        }

    @staticmethod
    async def _send_notification(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: SendPetitionSummaryFinishedNotificationJob._send_notification_sync(
                payload
            ),
        )

    @staticmethod
    def _send_notification_sync(payload: _Payload) -> None:
        use_case = SendPetitionSummaryFinishedNotificationUseCase(
            push_notification_provider=OneSignalPushNotificationProvider()
        )
        use_case.execute(
            account_id=Id.create(payload.account_id),
            analysis_id=Id.create(payload.analysis_id),
        )
