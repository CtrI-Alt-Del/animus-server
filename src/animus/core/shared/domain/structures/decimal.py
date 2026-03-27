from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class Decimal(Structure):
    value: float

    @classmethod
    def create(cls, value: float) -> 'Decimal':
        return cls(value=value)
