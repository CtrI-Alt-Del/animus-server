from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.auth.domain.events import PasswordResetRequestEvent
from animus.core.auth.domain.structures import Email, Otp
from animus.core.notification.use_cases.send_password_reset_email_use_case import (
    SendPasswordResetEmailUseCase,
)
from animus.providers.notification import ResendEmailSenderProvider


@dataclass(frozen=True)
class _Payload:
    account_email: Email
    account_email_otp: Otp


class SendPasswordResetEmailJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='send-password-reset-email',
            trigger=TriggerEvent(
                event=PasswordResetRequestEvent.name,
            ),
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                SendPasswordResetEmailJob._normalize_payload,
                data,
            )

            payload = _Payload(
                account_email=Email.create(str(normalized_data['account_email'])),
                account_email_otp=Otp.create(str(normalized_data['account_email_otp'])),
            )

            await context.step.run(
                'send_password_reset_email',
                SendPasswordResetEmailJob._send_password_reset_email,
                payload,
            )

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {
            'account_email': str(data['account_email']),
            'account_email_otp': str(data['account_email_otp']),
        }

    @staticmethod
    async def _send_password_reset_email(payload: _Payload) -> None:
        use_case = SendPasswordResetEmailUseCase(
            email_sender_provider=ResendEmailSenderProvider(),
        )
        use_case.execute(
            account_email=payload.account_email.value,
            otp=payload.account_email_otp.value,
        )
