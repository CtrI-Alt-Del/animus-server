from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.hash_provider import HashProvider
from animus.core.auth.use_cases.reset_password_use_case import ResetPasswordUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.providers_pipe import ProvidersPipe


class _Body(BaseModel):
    account_id: str
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
            hash_provider: Annotated[
                HashProvider, Depends(ProvidersPipe.get_hash_provider)
            ],
        ) -> None:
            use_case = ResetPasswordUseCase(
                accounts_repository=accounts_repository, hash_provider=hash_provider
            )
            return use_case.execute(
                account_id=body.account_id, new_password=body.new_password
            )
