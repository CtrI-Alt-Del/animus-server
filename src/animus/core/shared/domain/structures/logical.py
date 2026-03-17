from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class Logical(Structure):
    value: bool

    @classmethod
    def create(cls, value: bool) -> 'Logical':
        return cls(value=value)

    @classmethod
    def create_true(cls) -> 'Logical':
        return cls(value=True)

    @classmethod
    def create_false(cls) -> 'Logical':
        return cls(value=False)

    def invert(self) -> 'Logical':
        return Logical(value=not self.value)

    @property
    def is_true(self) -> bool:
        return self.value

    @property
    def is_false(self) -> bool:
        return not self.value
