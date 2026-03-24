from fastapi import APIRouter

from animus.rest.controllers.auth import (
    ResendVerificationEmailController,
    SignUpController,
    VerifyEmailController,
)
from animus.rest.controllers.auth.sign_in_with_google_controller import SignInWithGoogleController


class AuthRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/auth', tags=['auth'])

        SignUpController.handle(router)
        VerifyEmailController.handle(router)
        ResendVerificationEmailController.handle(router)
        SignInWithGoogleController.handle(router)

        return router
