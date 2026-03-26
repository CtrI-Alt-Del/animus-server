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
                'ordenacao': 'Text',
                'orgaos': orgaos,
                'pagina': page,
                'tipos': tipos,
            }
        }
        #@OTODO:colocar tipagem no metodo
        pangea_bnp_precedents = self._client.post(
            path='api/v1/precedentes', body=payload
        ).body
        precedents: list[Precedent] = []
        for pangea_bnp_precedent in pangea_bnp_precedents:
            try:
                precedent = PangeaBnpPrecedentMapper.to_entity(pangea_bnp_precedent)
                precedents.append(precedent)
            except Exception as error:
                print(error)
        return PagePaginationResponse[Precedent](
            items=precedents,
            total=len(precedents),
            page=page,
            page_size=page_size
        )
