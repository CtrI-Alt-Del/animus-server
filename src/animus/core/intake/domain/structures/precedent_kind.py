from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class PrecedentKindValue(StrEnum):
    SUM = 'SUM'
    SV = 'SV'
    OJ = 'OJ'
    RG = 'RG'
    RR = 'RR'
    TR = 'TR'
    IRDR = 'IRDR'
    IAC = 'IAC'
    PUIL = 'PUIL'
    ADI = 'ADI'
    ADC = 'ADC'
    ADO = 'ADO'
    ADPF = 'ADPF'
    NT = 'NT'
    GR = 'GR'
    CONT = 'CONT'
    SIRDR = 'SIRDR'
    IRR ='IRR'
    CT = 'CT'


@structure
class PrecedentKind(Structure):
    value: PrecedentKindValue

    @classmethod
    def create(cls, value: PrecedentKindValue | str) -> 'PrecedentKind':
        if isinstance(value, PrecedentKindValue):
            return cls(value=value)

        try:
            precedent_kind_value = PrecedentKindValue(value.upper())
        except ValueError as error:
            raise ValidationError(f'Tipo de precedente invalido: {value}') from error

        return cls(value=precedent_kind_value)

    @property
    def dto(self) -> str:
        return self.value.value
