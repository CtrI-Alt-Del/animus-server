from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class PrecedentStatusValue(StrEnum):
    VIGENTE = 'vigente'
    TRANSITADO_EM_JULGADO = 'transitado em julgado'


@structure
class PrecedentStatus(Structure):
    value: PrecedentStatusValue

    @classmethod
    def create(cls, value: PrecedentStatusValue | str) -> 'PrecedentStatus':
        if isinstance(value, PrecedentStatusValue):
            return cls(value=value)

        normalized_value = value.strip().lower()

        try:
            precedent_status_value = PrecedentStatusValue(normalized_value)
        except ValueError as error:
            raise ValidationError(f'Status de precedente invalido: {value}') from error

        return cls(value=precedent_status_value)

    @property
    def dto(self) -> str:
        return self.value.value
