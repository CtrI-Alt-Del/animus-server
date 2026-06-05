from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class LegalAreaValue(StrEnum):
    CONSTITUCIONAL = 'CONSTITUCIONAL'
    ADMINISTRATIVO = 'ADMINISTRATIVO'
    TRIBUTARIO = 'TRIBUTARIO'
    PREVIDENCIARIO = 'PREVIDENCIARIO'
    CIVIL = 'CIVIL'
    FAMILIA_E_SUCESSOES = 'FAMILIA_E_SUCESSOES'
    CONSUMIDOR = 'CONSUMIDOR'
    EMPRESARIAL = 'EMPRESARIAL'
    TRABALHISTA = 'TRABALHISTA'
    PENAL = 'PENAL'
    AMBIENTAL = 'AMBIENTAL'
    PROCESSUAL = 'PROCESSUAL'


@structure
class LegalArea(Structure):
    value: LegalAreaValue

    @classmethod
    def create(cls, value: str) -> 'LegalArea':
        try:
            legal_area_value = LegalAreaValue(value.upper())
        except ValueError as error:
            raise ValidationError(f'Area juridica invalida: {value}') from error

        return cls(value=legal_area_value)

    @property
    def dto(self) -> str:
        return self.value.value
