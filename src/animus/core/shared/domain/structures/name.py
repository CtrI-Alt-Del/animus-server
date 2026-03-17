from pydantic import ValidationError
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class Name(Structure):
    value: str

    @staticmethod
    def create(value: str) -> 'Name':
        if value.isspace() or len(value) < 3:
            raise ValidationError(
                f'Name must be at least 3 characters long and not contain spaces, got {value}'
            )
        return Name(value=value)
