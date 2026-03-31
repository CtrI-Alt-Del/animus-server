from dataclasses import field

from animus.core.shared.domain.decorators import dto


def _default_strings() -> list[str]:
    return []


@dto
class AnalysisPrecedentsSearchFiltersDto:
    courts: list[str] = field(default_factory=_default_strings)
    precedent_kinds: list[str] = field(default_factory=_default_strings)
    limit: int = 10
