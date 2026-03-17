from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Decimal(Structure):
    value: float

    @classmethod
    def create(cls, value: float) -> 'Decimal':
        if value < 0.0:
            raise ValidationError(
                f'Value must be greater than or equal to 0.0, got {value}'
            )

        return cls(value=value)
