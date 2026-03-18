from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Name(Structure):
    value: str

    @staticmethod
    def create(value: str) -> 'Name':
        normalized_value = value.strip()

        if len(normalized_value) < 2:
            raise ValidationError(
                f'Nome deve ter pelo menos 2 caracteres, recebido: {value}'
            )

        return Name(value=normalized_value)
