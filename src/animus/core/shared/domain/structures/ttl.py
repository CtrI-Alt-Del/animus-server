from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Ttl(Structure):
    seconds: int

    @classmethod
    def create(cls, seconds: int) -> 'Ttl':
        if seconds <= 0:
            raise ValidationError(
                f'TTL invalido: segundos deve ser maior que 0, recebido: {seconds}'
            )

        return cls(seconds=seconds)

    @property
    def dto(self) -> int:
        return self.seconds
