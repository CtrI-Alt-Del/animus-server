from animus.core.shared.domain.decorators import dto


@dto
class AnalysisPrecedentApplicabilityFeedbackDto:
    analysis_precedent_id: str
    applicability_level: int
    is_from_human: bool
    created_at: str
