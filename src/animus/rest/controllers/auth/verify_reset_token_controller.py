from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.email_verification_provider import (
    EmailVerificationProvider,
)
from animus.core.auth.use_cases.verify_reset_token_use_case import (
    VerifyResetTokenUseCase,
)
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.providers_pipe import ProvidersPipe


class _Body(BaseModel):
    token: str


class VerifyResetTokenController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/passwrod/verify-reset-token',
            status_code=200,
        )
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            email_verification_provider: Annotated[
                EmailVerificationProvider,
                Depends(ProvidersPipe.get_email_verification_provider),
            ],
        ):
            use_case = VerifyResetTokenUseCase(
                accounts_repository=accounts_repository,
                email_verification_provider=email_verification_provider,
            )
            return use_case.execute(body.token)
