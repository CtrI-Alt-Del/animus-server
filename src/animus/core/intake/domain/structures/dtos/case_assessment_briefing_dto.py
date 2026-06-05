from animus.core.shared.domain.decorators import dto


@dto
class CaseAssessmentBriefingDto:
    analysis_id: str
    legal_area: str
    court_jurisdiction: str
    main_claims: str
    intended_thesis: str
