from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class Text(Structure):
    value: str

    @staticmethod
    def create(value: str) -> 'Text':
        return Text(value=value)
