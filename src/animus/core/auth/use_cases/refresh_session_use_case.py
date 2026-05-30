from animus.core.auth.domain.errors import (
    AccountInactiveError,
    AccountNotVerifiedError,
    InvalidRefreshTokenError,
)
from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import AccountsRepository, JwtProvider
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Text


class RefreshSessionUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        jwt_provider: JwtProvider,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._jwt_provider = jwt_provider

    def execute(self, refresh_token: str) -> SessionDto:
        try:
            token = Text.create(refresh_token)
        except ValidationError as error:
            raise InvalidRefreshTokenError from error

        try:
            payload = self._jwt_provider.decode(token)
        except Exception as error:
            raise InvalidRefreshTokenError from error

        if payload.get('type') != 'refresh':
            raise InvalidRefreshTokenError

        subject = payload.get('sub')
        if subject is None:
            raise InvalidRefreshTokenError

        try:
            account_id = Id.create(subject)
        except ValidationError as error:
            raise InvalidRefreshTokenError from error

        account = self._accounts_repository.find_by_id(account_id)
        if account is None:
            raise InvalidRefreshTokenError

        if account.is_verified.is_false:
            raise AccountNotVerifiedError

        if account.is_active.is_false:
            raise AccountInactiveError

        return self._jwt_provider.encode(Text.create(account.id.value)).dto
