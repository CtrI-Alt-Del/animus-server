from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class PrecedentStatusValue(StrEnum):
    TRANSITADO_EM_JULGADO = 'transitado em julgado'
    VIGENTE = 'vigente'
    AFETADO = 'afetado'
    CONTROVERSIA_VINCULADA = 'controversia vinculada / vinculado ao tema stf'
    CANCELADO = 'cancelado'
    NAO_ADMITIDO = 'nao admitido'
    CONTROVERSIA_CANCELADA = 'controversia cancelada'
    SEM_STATUS = '—'


@structure
class PrecedentStatus(Structure):
    value: PrecedentStatusValue

    @classmethod
    def create(cls, value: PrecedentStatusValue | str) -> 'PrecedentStatus':
        if isinstance(value, PrecedentStatusValue):
            return cls(value=value)

        normalized_value = value.strip().lower()

        aliases = {
            'controvérsia vinculada / vinculado ao tema stf': PrecedentStatusValue.CONTROVERSIA_VINCULADA,
            'controversia vinculada / vinculado ao tema stf': PrecedentStatusValue.CONTROVERSIA_VINCULADA,
            'não admitido': PrecedentStatusValue.NAO_ADMITIDO,
            'nao admitido': PrecedentStatusValue.NAO_ADMITIDO,
            'controvérsia cancelada': PrecedentStatusValue.CONTROVERSIA_CANCELADA,
            'controversia cancelada': PrecedentStatusValue.CONTROVERSIA_CANCELADA,
            '— (sem status)': PrecedentStatusValue.SEM_STATUS,
            '(sem status)': PrecedentStatusValue.SEM_STATUS,
            '-': PrecedentStatusValue.SEM_STATUS,
        }

        mapped_value = aliases.get(normalized_value)
        if mapped_value is not None:
            return cls(value=mapped_value)

        try:
            precedent_status_value = PrecedentStatusValue(normalized_value)
        except ValueError as error:
            raise ValidationError(f'Status de precedente invalido: {value}') from error

        return cls(value=precedent_status_value)

    @property
    def dto(self) -> str:
        return self.value.value
