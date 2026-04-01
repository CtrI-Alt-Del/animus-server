from fastapi import APIRouter

from animus.rest.controllers.auth import (
    GetAccountController,
    ResendVerificationEmailController,
    SignInController,
    SignUpController,
    VerifyEmailController,
)
from animus.rest.controllers.auth.forgot_password_controller import ForgotPasswordController
from animus.rest.controllers.auth.reset_password_controller import ResetPasswordController
from animus.rest.controllers.auth.sign_in_with_google_controller import (
    SignInWithGoogleController,
)
from animus.rest.controllers.auth.verify_reset_token_controller import VerifyResetTokenController


class AuthRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/auth', tags=['auth'])

        SignInController.handle(router)
        SignUpController.handle(router)
        VerifyEmailController.handle(router)
        ResendVerificationEmailController.handle(router)
        SignInWithGoogleController.handle(router)
        GetAccountController.handle(router)
        ForgotPasswordController.handle(router)
        VerifyResetTokenController.handle(router)
        ResetPasswordController.handle(router)

        return router
