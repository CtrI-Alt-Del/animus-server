from typing import Any
from animus.core.shared.domain.abstracts.structure import Structure
from animus.core.shared.domain.decorators.structure import structure
from animus.rest.pangea.services.models.pangea_bnp_aggregation import (
    PangeaBnpAggregation,
)
from animus.rest.pangea.services.models.pangea_bnp_process import (
    PangeaBnpPrecedentProcess,
)


@structure
class PangeaBnpResponse(Structure):
    aggs_especies: list[PangeaBnpAggregation]
    aggs_orgaos: list[PangeaBnpAggregation]
    posição_final: int
    posição_inicial: int
    resultados: list[PangeaBnpPrecedentProcess]
    total: int

    @classmethod
    def create(cls, **data: Any) -> 'PangeaBnpResponse':
        return cls(
            aggs_especies=[
                PangeaBnpAggregation.create(**agg)
                for agg in data.get('aggsEspecies', [])
            ],
            aggs_orgaos=[
                PangeaBnpAggregation.create(**agg) for agg in data.get('aggsOrgaos', [])
            ],
            posição_final=int(data.get('posição_final', 0)),
            posição_inicial=int(data.get('posição_inicial', 0)),
            resultados=data.get('resultados', []),
            total=int(data.get('total', 0)),
        )
