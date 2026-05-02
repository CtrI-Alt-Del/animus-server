from pydantic import BaseModel, Field


class AnalysisPrecedentLegalFeaturesOutput(BaseModel):
    central_issue_match: int
    structural_issue_match: int
    context_compatibility: int
    is_lateral_topic: int
    is_accessory_topic: int


class AnalysisPrecedentSynthesisItemOutput(BaseModel):
    court: str
    kind: str
    number: int
    synthesis: str
    applicability_level: int = Field(
        ge=0,
        le=2,
        description='0 = não aplicável, 1 = possivelmente aplicável, 2 = aplicável',
    )
    legal_features: AnalysisPrecedentLegalFeaturesOutput


class AnalysisPrecedentsSynthesisOutput(BaseModel):
    items: list[AnalysisPrecedentSynthesisItemOutput]
