from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from animus.core.auth.interfaces import (
    AccountsRepository,
    EmailVerificationProvider,
    JwtProvider,
)
from animus.core.auth.use_cases import VerifyEmailUseCase
from animus.pipes import DatabasePipe, ProvidersPipe
from animus.rest.controllers.auth.constants.verify_email_success_html import (
    VERIFY_EMAIL_SUCCESS_HTML,
)


class VerifyEmailController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get('/verify-email', status_code=200, response_class=HTMLResponse)
        def _(
            token: Annotated[str, Query(min_length=1)],
            accounts_repository: Annotated[
                AccountsRepository,
                Depends(DatabasePipe.get_accounts_repository_from_request),
            ],
            email_verification_provider: Annotated[
                EmailVerificationProvider,
                Depends(ProvidersPipe.get_email_verification_provider),
            ],
            jwt_provider: Annotated[
                JwtProvider, Depends(ProvidersPipe.get_jwt_provider)
            ],
        ) -> HTMLResponse:
            use_case = VerifyEmailUseCase(
                accounts_repository=accounts_repository,
                email_verification_provider=email_verification_provider,
                jwt_provider=jwt_provider,
            )
            use_case.execute(token=token)
            return HTMLResponse(content=VERIFY_EMAIL_SUCCESS_HTML)
