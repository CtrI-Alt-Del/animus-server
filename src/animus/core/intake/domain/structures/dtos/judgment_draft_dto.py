from animus.core.shared.domain.decorators import dto


@dto
class JudgmentDraftDto:
    analysis_id: str
    content: str
