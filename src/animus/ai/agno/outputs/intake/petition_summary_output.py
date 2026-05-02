from pydantic import BaseModel, Field


class PetitionSummaryOutput(BaseModel):
    case_summary: str
    legal_issue: str
    central_question: str
    relevant_laws: list[str]
    key_facts: list[str]
    search_terms: list[str]
    type_of_action: str | None = None
    secondary_legal_issues: list[str] = Field(default_factory=list)
    alternative_questions: list[str] = Field(default_factory=list)
    jurisdiction_issue: str | None = None
    standing_issue: str | None = None
    requested_relief: list[str] = Field(default_factory=list)
    procedural_issues: list[str] = Field(default_factory=list)
    excluded_or_accessory_topics: list[str] = Field(default_factory=list)
