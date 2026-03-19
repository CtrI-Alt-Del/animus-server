import resend

from animus.constants import Env
from animus.core.auth.domain.structures.email import Email
from animus.core.notification.interfaces import EmailSenderProvider
from animus.core.shared.domain.structures import Text
from animus.providers.notification.email_sender.constants.email_verification_html import (
    EMAIL_VERIFICATION_HTML,
)


class ResendEmailSenderProvider(EmailSenderProvider):
    def send_account_verification_email(
        self,
        account_email: Email,
        verification_token: Text,
    ) -> None:
        resend.api_key = Env.RESEND_API_KEY

        verification_url = f'{Env.ANIMUS_SERVER_URL}/auth/verify-email?token={verification_token.value}'
        html = EMAIL_VERIFICATION_HTML.format(verification_url=verification_url)

        resend.Emails.send(
            {
                'from': Env.RESEND_SENDER_EMAIL,
                'to': [account_email.value],
                'subject': 'Verifique seu email',
                'html': html,
                'text': (
                    f'Use o link abaixo para verificar seu email:\n{verification_url}\n'
                ),
            }
        )
