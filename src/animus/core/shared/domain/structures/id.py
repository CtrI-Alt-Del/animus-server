import re
from ulid import ULID

from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.errors import ValidationError

ULID_REGEX = re.compile(r'^[0-9A-HJKMNP-TV-Z]{26}$')


@structure
class Id(Structure):
    value: str

    @staticmethod
    def create(id: str | None = None) -> 'Id':
        if id is None:
            return Id(value=str(ULID()))

        if not ULID_REGEX.match(id):
            raise ValidationError(f'ULID inválido: {id}')

        return Id(value=id)
