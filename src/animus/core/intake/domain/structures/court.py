from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class CourtValue(StrEnum):
    STF = 'STF'
    STJ = 'STJ'
    TST = 'TST'
    TSE = 'TSE'
    STM = 'STM'
    TNU = 'TNU'
    TRFS6 = 'TRFS6'
    TJS27 = 'TJS27'
    TJAC = 'TJAC'
    TJAL = 'TJAL'
    TJAP = 'TJAP'
    TJAM = 'TJAM'
    TJBA = 'TJBA'
    TJCE = 'TJCE'
    TJDF = 'TJDF'
    TJES = 'TJES'
    TJGO = 'TJGO'
    TJMA = 'TJMA'
    TJMT = 'TJMT'
    TJMS = 'TJMS'
    TJMG = 'TJMG'
    TJPA = 'TJPA'
    TJPB = 'TJPB'
    TJPR = 'TJPR'
    TJPE = 'TJPE'
    TJPI = 'TJPI'
    TJRJ = 'TJRJ'
    TJRN = 'TJRN'
    TJRS = 'TJRS'
    TJRO = 'TJRO'
    TJRR = 'TJRR'
    TJSC = 'TJSC'
    TJSP = 'TJSP'
    TJSE = 'TJSE'
    TJTO = 'TJTO'
    TRTS24 = 'TRTS24'
    TRT1 = 'TRT1'
    TRT2 = 'TRT2'
    TRT3 = 'TRT3'
    TRT4 = 'TRT4'
    TRT5 = 'TRT5'
    TRT6 = 'TRT6'
    TRT7 = 'TRT7'
    TRT8 = 'TRT8'
    TRT9 = 'TRT9'
    TRT10 = 'TRT10'
    TRT11 = 'TRT11'
    TRT12 = 'TRT12'
    TRT13 = 'TRT13'
    TRT14 = 'TRT14'
    TRT15 = 'TRT15'
    TRT16 = 'TRT16'
    TRT17 = 'TRT17'
    TRT18 = 'TRT18'
    TRT19 = 'TRT19'
    TRT20 = 'TRT20'
    TRT21 = 'TRT21'
    TRT22 = 'TRT22'
    TRT23 = 'TRT23'
    TRT24 = 'TRT24'


@structure
class Court(Structure):
    value: CourtValue

    @classmethod
    def create(cls, value: str) -> 'Court':
        try:
            court_value = CourtValue(value.upper())
        except ValueError as error:
            raise ValidationError(f'Tribunal invalido: {value}') from error

        return cls(value=court_value)

    @property
    def dto(self) -> str:
        return self.value.value
