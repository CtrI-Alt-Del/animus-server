from pydantic import BaseModel


class SecondInstanceJudgmentDraftOutput(BaseModel):
    report: str
    merit_analysis: str
    precedent_adherence_analysis: str
    ruling: list[str]
    preliminary_issues: str | None = None
    no_applicable_precedent_notice: str | None = None
