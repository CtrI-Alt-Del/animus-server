from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.interfaces import (
    AccountsRepository,
    EmailVerificationProvider,
    HashProvider,
)
from animus.core.auth.use_cases import SignUpUseCase
from animus.core.shared.interfaces import Broker
from animus.pipes import DatabasePipe, ProvidersPipe, PubSubPipe


class _Body(BaseModel):
    name: str
    email: str
    password: str


class SignUpController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/sign-up', status_code=201, response_model=AccountDto)
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            hash_provider: Annotated[
                HashProvider, Depends(ProvidersPipe.get_hash_provider)
            ],
            email_verification_provider: Annotated[
                EmailVerificationProvider,
                Depends(ProvidersPipe.get_email_verification_provider),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> AccountDto:
            use_case = SignUpUseCase(
                accounts_repository=accounts_repository,
                hash_provider=hash_provider,
                email_verification_provider=email_verification_provider,
                broker=broker,
            )
            return use_case.execute(
                name=body.name,
                email=body.email,
                password=body.password,
            )
