from typing import Annotated

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.interfaces import AccountsRepository, JwtProvider
from animus.core.auth.use_cases import UpdateAccountUseCase
from animus.pipes import AuthPipe, DatabasePipe, ProvidersPipe


class _Body(BaseModel):
    name: str


class UpdateAccountController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch('/account', status_code=200, response_model=AccountDto)
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            jwt_provider: Annotated[
                JwtProvider, Depends(ProvidersPipe.get_jwt_provider)
            ],
            authorization: Annotated[str | None, Header(alias='Authorization')] = None,
        ) -> AccountDto:
            account_id = AuthPipe.get_account_id_from_request(
                authorization=authorization,  # type: ignore
                jwt_provider=jwt_provider,
                accounts_repository=accounts_repository,
            )
            use_case = UpdateAccountUseCase(accounts_repository=accounts_repository)
            return use_case.execute(account_id=account_id.value, name=body.name)
