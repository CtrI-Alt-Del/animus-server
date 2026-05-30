from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import AccountsRepository, JwtProvider
from animus.core.auth.use_cases import RefreshSessionUseCase
from animus.pipes import DatabasePipe, ProvidersPipe


class _Body(BaseModel):
    refresh_token: str


class RefreshSessionController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/refresh', status_code=200, response_model=SessionDto)
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            jwt_provider: Annotated[
                JwtProvider, Depends(ProvidersPipe.get_jwt_provider)
            ],
        ) -> SessionDto:
            use_case = RefreshSessionUseCase(
                accounts_repository=accounts_repository,
                jwt_provider=jwt_provider,
            )
            return use_case.execute(refresh_token=body.refresh_token)
