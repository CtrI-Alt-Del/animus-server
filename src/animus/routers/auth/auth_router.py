from fastapi import APIRouter

from animus.rest.controllers.auth import (
    GetAccountController,
    ResendResetPasswordOtpController,
    ResendVerificationEmailController,
    SignInController,
    SignUpController,
    UpdateAccountController,
    VerifyEmailController,
    VerifyResetPasswordOtpController,
)
from animus.rest.controllers.auth.forgot_password_controller import (
    ForgotPasswordController,
)
from animus.rest.controllers.auth.reset_password_controller import (
    ResetPasswordController,
)
from animus.rest.controllers.auth.sign_in_with_google_controller import (
    SignInWithGoogleController,
)


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
        ResendResetPasswordOtpController.handle(router)
        VerifyResetPasswordOtpController.handle(router)
        ResetPasswordController.handle(router)
        UpdateAccountController.handle(router)

        return router
