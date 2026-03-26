from typing import NamedTuple


class CacheKeys(NamedTuple):
    EMAIL_VERIFICATION = 'auth:email_verification'
    EMAIL_VERIFICATION_ATTEMPTS = 'auth:email_verification_attempts'

    def get_email_verification(self, email: str) -> str:
        return f'{self.EMAIL_VERIFICATION}:{email}'

    def get_email_verification_attempts(self, email: str) -> str:
        return f'{self.EMAIL_VERIFICATION_ATTEMPTS}:{email}'
