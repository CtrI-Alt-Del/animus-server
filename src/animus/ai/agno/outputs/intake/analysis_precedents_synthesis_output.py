from pydantic import BaseModel


class AnalysisPrecedentSynthesisItemOutput(BaseModel):
    court: str
    kind: str
    number: int
    synthesis: str


class AnalysisPrecedentsSynthesisOutput(BaseModel):
    items: list[AnalysisPrecedentSynthesisItemOutput]
