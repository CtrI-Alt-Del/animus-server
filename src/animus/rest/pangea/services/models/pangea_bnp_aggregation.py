from typing import Any
from animus.core.shared.domain.abstracts.structure import Structure
from animus.core.shared.domain.decorators.structure import structure


@structure
class PangeaBnpAggregation(Structure):
    tipo: str
    total: int

    @classmethod
    def create(cls, **data: Any) -> 'PangeaBnpAggregation':
        return cls(tipo=str(data.get('tipo', '')), total=int(data.get('total', 0)))
