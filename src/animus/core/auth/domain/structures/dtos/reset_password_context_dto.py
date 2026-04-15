from animus.core.shared.domain.decorators import dto


@dto
class ResetPasswordContextDto:
    reset_context: str
