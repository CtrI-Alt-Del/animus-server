from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from animus.core.auth.interfaces import AccountsRepository
from animus.database.sqlalchemy.repositories.auth import SqlalchemyAccountsRepository


def get_sqlalchemy_session_from_request(request: Request) -> Session:
    return request.state.sqlalchemy_session


class DatabasePipe:
    @staticmethod
    def get_accounts_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> AccountsRepository:
        return SqlalchemyAccountsRepository(sqlalchemy)
