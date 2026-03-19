from fastapi import APIRouter

from animus.rest.controllers.auth import (
    ResendVerificationEmailController,
    SignUpController,
    VerifyEmailController,
)


class AuthRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/auth', tags=['auth'])

        SignUpController.handle(router)
        VerifyEmailController.handle(router)
        ResendVerificationEmailController.handle(router)

        return router
