from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from animus.constants import Env
from animus.core.auth.domain.errors import InvalidEmailVerificationTokenError
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces import EmailVerificationProvider
from animus.core.shared.domain.structures import Logical, Text


class ItsdangerousEmailVerificationProvider(EmailVerificationProvider):
    @staticmethod
    def _serializer() -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(Env.EMAIL_VERIFICATION_SECRET_KEY)

    def generate_verification_token(self, account_email: Email) -> Text:
        token = self._serializer().dumps(
            account_email.value,
            salt=Env.EMAIL_VERIFICATION_SALT,
        )
        return Text.create(token)

    def verify_verification_token(self, verification_token: Text) -> Logical:
        try:
            self._serializer().loads(
                verification_token.value,
                salt=Env.EMAIL_VERIFICATION_SALT,
                max_age=Env.EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS,
            )
        except (BadSignature, SignatureExpired):
            return Logical.create_false()

        return Logical.create_true()

    def decode_email_from_token(self, verification_token: Text) -> Email:
        try:
            value = self._serializer().loads(
                verification_token.value,
                salt=Env.EMAIL_VERIFICATION_SALT,
                max_age=Env.EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS,
            )
        except (BadSignature, SignatureExpired) as error:
            raise InvalidEmailVerificationTokenError from error

        return Email.create(str(value))

    def invalidate_verification_token(self, verification_token: Text) -> None:
        _ = verification_token
