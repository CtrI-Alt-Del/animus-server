from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from animus.constants.env import Env
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases import ResendResetPasswordOtpUseCase
from animus.core.shared.domain.structures import Ttl
from animus.core.shared.interfaces import Broker, CacheProvider, OtpProvider
from animus.pipes import DatabasePipe, ProvidersPipe, PubSubPipe


class _Body(BaseModel):
    email: str


class ResendResetPasswordOtpController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/password/resend-reset-otp', status_code=204)
        def _(
            body: _Body,
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            otp_provider: Annotated[
                OtpProvider, Depends(ProvidersPipe.get_otp_provider)
            ],
            cache_provider: Annotated[
                CacheProvider,
                Depends(ProvidersPipe.get_cache_provider),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> Response:
            use_case = ResendResetPasswordOtpUseCase(
                accounts_repository=accounts_repository,
                otp_provider=otp_provider,
                cache_provider=cache_provider,
                broker=broker,
                reset_password_otp_ttl=Ttl.create(Env.RESET_PASSWORD_OTP_TTL_SECONDS),
                reset_password_otp_resend_cooldown_ttl=Ttl.create(
                    Env.RESET_PASSWORD_OTP_RESEND_COOLDOWN_SECONDS
                ),
            )
            use_case.execute(email=body.email)
            return Response(status_code=204)
