from datetime import datetime, UTC
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class Datetime(Structure):
    value: datetime

    @classmethod
    def create(cls, value: datetime | str) -> 'Datetime':
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return cls(value=value)

    @classmethod
    def create_at_now(cls) -> 'Datetime':
        return cls(value=datetime.now(UTC))
