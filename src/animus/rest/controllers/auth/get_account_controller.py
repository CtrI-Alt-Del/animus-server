from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases import GetAccountUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes import AuthPipe, DatabasePipe


class GetAccountController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/me',
            response_model=AccountDto,
            status_code=200,
        )
        def _(
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            accounts_repository: Annotated[AccountsRepository, Depends(DatabasePipe.get_accounts_repository_from_request)],
        ) -> AccountDto:
            use_case = GetAccountUseCase(accounts_repository)
            return use_case.execute(account_id)
