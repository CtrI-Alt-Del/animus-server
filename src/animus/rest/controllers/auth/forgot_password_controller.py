from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.use_cases.forgot_password_use_case import ForgotPasswordUseCase
from animus.core.shared.interfaces.broker import Broker
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.pubsub_pipe import PubSubPipe


class _Body(BaseModel):
    email: str


class ForgotPasswordController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/password/forgot',
            status_code=204,
        )
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> None:
            use_case = ForgotPasswordUseCase(
                accounts_repository=accounts_repository, broker=broker
            )
            return use_case.execute(body.email)
