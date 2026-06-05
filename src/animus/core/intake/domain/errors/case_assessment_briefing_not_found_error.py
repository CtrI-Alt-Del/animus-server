from animus.core.shared.domain.errors import NotFoundError


class CaseAssessmentBriefingNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Briefing da analise nao encontrado')
