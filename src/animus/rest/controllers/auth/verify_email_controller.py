from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import AccountsRepository, JwtProvider
from animus.core.auth.use_cases import VerifyEmailUseCase
from animus.core.shared.interfaces import CacheProvider
from animus.pipes import DatabasePipe, ProvidersPipe


class _Body(BaseModel):
    email: str
    otp: str


class VerifyEmailController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/verify-email', status_code=200, response_model=SessionDto)
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
            jwt_provider: Annotated[
                JwtProvider, Depends(ProvidersPipe.get_jwt_provider)
            ],
        ) -> SessionDto:
            use_case = VerifyEmailUseCase(
                accounts_repository=accounts_repository,
                cache_provider=cache_provider,
                jwt_provider=jwt_provider,
            )
            return use_case.execute(email=body.email, otp=body.otp)
