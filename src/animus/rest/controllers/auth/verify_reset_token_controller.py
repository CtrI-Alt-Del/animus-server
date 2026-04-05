from typing import Annotated

from fastapi import APIRouter, Depends, Query

from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.email_verification_provider import (
    EmailVerificationProvider,
)
from animus.core.auth.use_cases.verify_reset_token_use_case import (
    VerifyResetTokenUseCase,
)
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.providers_pipe import ProvidersPipe


class VerifyResetTokenController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/password/verify-reset-token',
            status_code=200,
        )
        def _(
            token: Annotated[str, Query()],
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            email_verification_provider: Annotated[
                EmailVerificationProvider,
                Depends(ProvidersPipe.get_email_verification_provider),
            ],
        ) -> dict[str, str]:
            use_case = VerifyResetTokenUseCase(
                accounts_repository=accounts_repository,
                email_verification_provider=email_verification_provider,
            )
            account_id = use_case.execute(token)
            return {'account_id': account_id}
