from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.interfaces import AccountsRepository, HashProvider
from animus.core.auth.use_cases import ResetPasswordUseCase
from animus.core.shared.interfaces import CacheProvider
from animus.pipes import DatabasePipe, ProvidersPipe


class _Body(BaseModel):
    reset_context: str
    new_password: str


class ResetPasswordController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/password/reset',
            status_code=200,
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
            hash_provider: Annotated[
                HashProvider, Depends(ProvidersPipe.get_hash_provider)
            ],
        ) -> None:
            use_case = ResetPasswordUseCase(
                accounts_repository=accounts_repository,
                cache_provider=cache_provider,
                hash_provider=hash_provider,
            )
            return use_case.execute(
                reset_context=body.reset_context,
                new_password=body.new_password,
            )
