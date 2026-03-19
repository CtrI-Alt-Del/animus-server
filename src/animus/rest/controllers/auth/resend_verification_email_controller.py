from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from animus.core.auth.interfaces import AccountsRepository, EmailVerificationProvider
from animus.core.auth.use_cases import ResendVerificationEmailUseCase
from animus.core.shared.interfaces import Broker
from animus.pipes import DatabasePipe, ProvidersPipe, PubSubPipe


class _Body(BaseModel):
    email: str


class ResendVerificationEmailController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/resend-verification-email', status_code=204)
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            email_verification_provider: Annotated[
                EmailVerificationProvider,
                Depends(ProvidersPipe.get_email_verification_provider),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> Response:
            use_case = ResendVerificationEmailUseCase(
                accounts_repository=accounts_repository,
                email_verification_provider=email_verification_provider,
                broker=broker,
            )
            use_case.execute(email=body.email)
            return Response(status_code=204)
