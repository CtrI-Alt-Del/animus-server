from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class PrecedentEmbeddingFieldValue(StrEnum):
    TITLE = 'TITLE'
    THESIS = 'THESIS'
    ENUNCIATION = 'ENUNCIATION'


@structure
class PrecedentEmbeddingField(Structure):
    value: PrecedentEmbeddingFieldValue

    @classmethod
    def create(
        cls,
        value: str,
    ) -> 'PrecedentEmbeddingField':
        try:
            embedding_field_value = PrecedentEmbeddingFieldValue(value.upper())
        except ValueError as error:
            raise ValidationError(f'Campo de embedding invalido: {value}') from error

        return cls(value=embedding_field_value)

    @property
    def dto(self) -> str:
        return self.value.value
