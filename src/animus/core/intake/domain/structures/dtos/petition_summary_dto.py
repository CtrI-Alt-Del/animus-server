from dataclasses import field

from animus.core.shared.domain.decorators import dto


def _default_strings() -> list[str]:
    return []


@dto
class PetitionSummaryDto:
    case_summary: str
    legal_issue: str
    central_question: str
    relevant_laws: list[str]
    key_facts: list[str]
    search_terms: list[str]

    type_of_action: str | None = None
    secondary_legal_issues: list[str] = field(default_factory=_default_strings)
    alternative_questions: list[str] = field(default_factory=_default_strings)
    jurisdiction_issue: str | None = None
    standing_issue: str | None = None
    requested_relief: list[str] = field(default_factory=_default_strings)
    procedural_issues: list[str] = field(default_factory=_default_strings)
    excluded_or_accessory_topics: list[str] = field(default_factory=_default_strings)
