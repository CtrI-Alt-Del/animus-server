import resend

from animus.constants import Env
from animus.core.auth.domain.structures import Email, Otp
from animus.core.notification.interfaces import EmailSenderProvider
from animus.providers.notification.email_sender.constants.account_verification_email_template import (
    ACCOUNT_VERIFICATION_EMAIL_TEMPLATE,
)
from animus.providers.notification.email_sender.constants.reset_password_email_template import (
    RESET_PASSWORD_EMAIL_TEMPLATE,
)


class ResendEmailSenderProvider(EmailSenderProvider):
    def send_account_verification_email(
        self,
        account_email: Email,
        otp: Otp,
    ) -> None:
        resend.api_key = Env.RESEND_API_KEY
        html = ACCOUNT_VERIFICATION_EMAIL_TEMPLATE.replace('{{OTP_CODE}}', otp.value)

        resend.Emails.send(
            {
                'from': Env.RESEND_SENDER_EMAIL,
                'to': [account_email.value],
                'subject': 'Codigo de verificacao de email',
                'html': html,
            }
        )

    def send_password_reset_email(self, account_email: Email, otp: Otp) -> None:
        resend.api_key = Env.RESEND_API_KEY
        html = RESET_PASSWORD_EMAIL_TEMPLATE.replace('{{OTP_CODE}}', otp.value)

        resend.Emails.send(
            {
                'from': Env.RESEND_SENDER_EMAIL,
                'to': [account_email.value],
                'subject': 'Esqueci minha senha',
                'html': html,
            }
        )
