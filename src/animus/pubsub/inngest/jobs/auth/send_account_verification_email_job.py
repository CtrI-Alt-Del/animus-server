from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.domain.structures import Email
from animus.core.notification import SendAccountVerificationEmailUseCase
from animus.core.shared.domain.structures import Text
from animus.providers.notification import ResendEmailSenderProvider


@dataclass(frozen=True)
class _Payload:
    account_email: Email
    account_email_verification_token: Text


class SendAccountVerificationEmailJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='send-account-verification-email',
            trigger=TriggerEvent(
                event=EmailVerificationRequestedEvent.name,
            ),
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                SendAccountVerificationEmailJob._normalize_payload,
                data,
            )
            payload = _Payload(
                account_email=Email.create(str(normalized_data['account_email'])),
                account_email_verification_token=Text.create(
                    str(normalized_data['account_email_verification_token'])
                ),
            )

            await context.step.run(
                'send_account_verification_email',
                SendAccountVerificationEmailJob._send_account_verification_email,
                payload,
            )

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {
            'account_email': str(data['account_email']),
            'account_email_verification_token': str(
                data['account_email_verification_token']
            ),
        }

    @staticmethod
    async def _send_account_verification_email(payload: _Payload) -> None:
        use_case = SendAccountVerificationEmailUseCase(
            email_sender_provider=ResendEmailSenderProvider()
        )
        use_case.execute(
            account_email=payload.account_email.value,
            verification_token=payload.account_email_verification_token.value,
        )
