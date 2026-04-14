from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.constants.env import Env
from animus.core.auth.domain.structures.dtos import ResetPasswordContextDto
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases import VerifyResetPasswordOtpUseCase
from animus.core.shared.domain.structures import Ttl
from animus.core.shared.interfaces import CacheProvider
from animus.pipes import DatabasePipe, ProvidersPipe


class _Body(BaseModel):
    email: str
    otp: str


class VerifyResetPasswordOtpController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/password/verify-reset-otp',
            status_code=200,
            response_model=ResetPasswordContextDto,
        )
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            cache_provider: Annotated[
                CacheProvider,
                Depends(ProvidersPipe.get_cache_provider),
            ],
        ) -> ResetPasswordContextDto:
            use_case = VerifyResetPasswordOtpUseCase(
                accounts_repository=accounts_repository,
                cache_provider=cache_provider,
                reset_password_context_ttl=Ttl.create(
                    Env.RESET_PASSWORD_CONTEXT_TTL_SECONDS
                ),
            )
            return use_case.execute(email=body.email, otp=body.otp)
