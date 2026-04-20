from enum import IntEnum

from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.errors import ValidationError


class AnalysisPrecedentApplicabilityLevelValue(IntEnum):
    NOT_APPLICABLE = 0
    POSSIBLY_APPLICABLE = 1
    APPLICABLE = 2


@structure
class AnalysisPrecedentApplicabilityLevel(Structure):
    value: AnalysisPrecedentApplicabilityLevelValue

    @classmethod
    def create(
        cls,
        value: float | int | str | None,
    ) -> 'AnalysisPrecedentApplicabilityLevel':
        if value is None:
            return cls(value=AnalysisPrecedentApplicabilityLevelValue.NOT_APPLICABLE)

        if isinstance(value, str):
            by_name = {
                'NOT_APPLICABLE': AnalysisPrecedentApplicabilityLevelValue.NOT_APPLICABLE,
                'POSSIBLY_APPLICABLE': AnalysisPrecedentApplicabilityLevelValue.POSSIBLY_APPLICABLE,
                'APPLICABLE': AnalysisPrecedentApplicabilityLevelValue.APPLICABLE,
            }
            try:
                return cls(value=by_name[value])
            except KeyError as error:
                raise ValidationError(
                    f'Nivel de aplicabilidade invalido: {value}'
                ) from error

        if isinstance(value, int):
            try:
                by_ordinal = {
                    0: AnalysisPrecedentApplicabilityLevelValue.NOT_APPLICABLE,
                    1: AnalysisPrecedentApplicabilityLevelValue.POSSIBLY_APPLICABLE,
                    2: AnalysisPrecedentApplicabilityLevelValue.APPLICABLE,
                }
                return cls(value=by_ordinal[value])
            except KeyError as error:
                raise ValidationError(
                    f'Nivel de aplicabilidade invalido: {value}'
                ) from error

        similarity_percentage = value

        if similarity_percentage >= 85.0:
            return cls(value=AnalysisPrecedentApplicabilityLevelValue.APPLICABLE)

        if similarity_percentage >= 70.0:
            return cls(
                value=AnalysisPrecedentApplicabilityLevelValue.POSSIBLY_APPLICABLE
            )

        return cls(value=AnalysisPrecedentApplicabilityLevelValue.NOT_APPLICABLE)

    @property
    def dto(self) -> int:
        return self.value.value
