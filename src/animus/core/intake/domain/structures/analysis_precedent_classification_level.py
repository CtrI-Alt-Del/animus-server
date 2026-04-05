from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure


class AnalysisPrecedentClassificationLevelValue(StrEnum):
    APPLICABLE = 'APPLICABLE'
    POSSIBLY_APPLICABLE = 'POSSIBLY_APPLICABLE'
    NOT_APPLICABLE = 'NOT_APPLICABLE'


@structure
class AnalysisPrecedentClassificationLevel(Structure):
    value: AnalysisPrecedentClassificationLevelValue

    @classmethod
    def create(
        cls,
        applicability_percentage: float | None,
    ) -> 'AnalysisPrecedentClassificationLevel':
        if applicability_percentage is None:
            return cls(value=AnalysisPrecedentClassificationLevelValue.NOT_APPLICABLE)

        if applicability_percentage >= 85.0:
            return cls(value=AnalysisPrecedentClassificationLevelValue.APPLICABLE)

        if applicability_percentage >= 70.0:
            return cls(
                value=AnalysisPrecedentClassificationLevelValue.POSSIBLY_APPLICABLE
            )

        return cls(value=AnalysisPrecedentClassificationLevelValue.NOT_APPLICABLE)

    @property
    def dto(self) -> str:
        return self.value.value
