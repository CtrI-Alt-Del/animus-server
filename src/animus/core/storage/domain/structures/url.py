from urllib.parse import urlparse

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Url(Structure):
    value: str

    @classmethod
    def create(cls, value: str) -> 'Url':
        normalized_value = value.strip()
        parsed_url = urlparse(normalized_value)

        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValidationError(f'URL invalida: {value}')

        return cls(value=normalized_value)

    @property
    def dto(self) -> str:
        return self.value
