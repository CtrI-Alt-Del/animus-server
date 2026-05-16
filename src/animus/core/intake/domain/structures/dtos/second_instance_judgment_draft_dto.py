from animus.core.shared.domain.decorators import dto


@dto
class SecondInstanceJudgmentDraftDto:
    analysis_id: str
    content: str
