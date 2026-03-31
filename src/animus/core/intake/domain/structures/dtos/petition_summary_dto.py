from animus.core.shared.domain.decorators import dto


@dto
class PetitionSummaryDto:
    case_summary: str
    legal_issue: str
    central_question: str
    relevant_laws: list[str]
    key_facts: list[str]
    search_terms: list[str]
