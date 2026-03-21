from pydantic import BaseModel
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.notification import SendAccountVerificationEmailUseCase
from animus.providers.notification import ResendEmailSenderProvider


class _Payload(BaseModel):
    account_email: str
    account_email_verification_token: str


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

            await context.step.run(
                'send_account_verification_email',
                SendAccountVerificationEmailJob._send_account_verification_email,
                data,
            )

        return _

    @staticmethod
    async def _send_account_verification_email(
        data: dict[str, Any],
    ) -> None:
        normalized_payload = _Payload(
            account_email=str(data['account_email']),
            account_email_verification_token=str(
                data['account_email_verification_token']
            ),
        )
        use_case = SendAccountVerificationEmailUseCase(
            email_sender_provider=ResendEmailSenderProvider()
        )
        use_case.execute(
            account_email=normalized_payload.account_email,
            verification_token=normalized_payload.account_email_verification_token,
        )
