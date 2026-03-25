from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import AccountsRepository, HashProvider, JwtProvider
from animus.core.auth.use_cases import SignInUseCase
from animus.pipes import DatabasePipe, ProvidersPipe


class _Body(BaseModel):
    email: str
    password: str


class SignInController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/sign-in', status_code=200, response_model=SessionDto)
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            hash_provider: Annotated[
                HashProvider, Depends(ProvidersPipe.get_hash_provider)
            ],
            jwt_provider: Annotated[
                JwtProvider, Depends(ProvidersPipe.get_jwt_provider)
            ],
        ) -> SessionDto:
            use_case = SignInUseCase(
                accounts_repository=accounts_repository,
                hash_provider=hash_provider,
                jwt_provider=jwt_provider,
            )
            return use_case.execute(email=body.email, password=body.password)
