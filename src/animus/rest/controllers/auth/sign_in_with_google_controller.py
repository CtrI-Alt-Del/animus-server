from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import (
    AccountsRepository,
    OAuthProvider,
    JwtProvider,
)
from animus.core.auth.use_cases import SignInWithGoogleUseCase
from animus.pipes import DatabasePipe, ProvidersPipe


class _Body(BaseModel):
    id_token: str


class SignInWithGoogleController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/sign-up/google', status_code=201, response_model=SessionDto)
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            jwt_provider: Annotated[
                JwtProvider, 
                Depends(ProvidersPipe.get_jwt_provider)
            ],
            google_oauth_provider: Annotated[
                OAuthProvider, 
                Depends(ProvidersPipe.get_google_oauth_provider)
            ],
        ) -> SessionDto:
            use_case = SignInWithGoogleUseCase(
                accounts_repository=accounts_repository,
                jwt_provider=jwt_provider,
                google_oauth_provider=google_oauth_provider,
            )
            return use_case.execute(
                id_token=body.id_token
            )
