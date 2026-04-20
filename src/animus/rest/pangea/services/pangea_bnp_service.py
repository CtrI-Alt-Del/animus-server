from animus.constants.env import Env
from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.court import CourtValue
from animus.core.intake.domain.structures.precedent_kind import PrecedentKindValue
from animus.core.intake.interfaces.pangea_service import PangeaService
from animus.core.shared.interfaces.rest_client import RestClient
from animus.core.shared.responses.page_pagination_response import PagePaginationResponse
from animus.rest.pangea.services.mappers.pangea_bnp_precedent_mapper import (
    PangeaBnpPrecedentMapper,
)
from animus.rest.pangea.services.models.pangea_bnp_precedent import PangeaBnpResponse


class PangeaBnpService(PangeaService):
    def __init__(self, client: RestClient) -> None:
        self._client = client
        self._client.set_base_url(Env.PANGEA_SERVICE_URL)

    def fetch_precedents(
        self, page: int, page_size: int
    ) -> PagePaginationResponse[Precedent]:
        orgaos = [court.value for court in CourtValue]
        tipos = [kind.value for kind in PrecedentKindValue]
        payload = {
            'filtro': {
                'buscaGeral': '',
                'ordenacao': 'Text',
                'pagina': page,
                'tamanhoPagina': page_size,
                'tipos': tipos,
                'orgaos': orgaos,
            }
        }
        response_data = self._client.post(
            response_model=PangeaBnpResponse, path='api/v1/precedentes', body=payload
        ).body
        precedents: list[Precedent] = []
        if not response_data:
            return PagePaginationResponse(
                items=[], total=0, page=page, page_size=page_size
            )
        actual_page_size = (
            response_data.posicao_final - response_data.posicao_inicial
        ) + 1
        if actual_page_size <= 0:
            actual_page_size = page_size
        for model in response_data.resultados:
            try:
                precedent = PangeaBnpPrecedentMapper.to_entity(model)
                precedents.append(precedent)
            except Exception as error:  # noqa: BLE001
                print(
                    f'Erro ao processar precedente {getattr(model, "id", "S/ID")}: {error}'
                )

        return PagePaginationResponse[Precedent](
            items=precedents,
            total=response_data.total,
            page=page,
            page_size=actual_page_size,
        )
