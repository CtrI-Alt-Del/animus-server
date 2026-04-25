from pydantic import BaseModel


class AnalysisPrecedentApplicabilityClassificationItemOutput(BaseModel):
    precedent_id: str
    applicability_level: int
    confidence: str


class AnalysisPrecedentsApplicabilityClassificationOutput(BaseModel):
    items: list[AnalysisPrecedentApplicabilityClassificationItemOutput]
