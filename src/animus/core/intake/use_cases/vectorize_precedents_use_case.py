
from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.interfaces.pangea_service import PangeaService
from animus.core.intake.interfaces.precedent_embeddings_provider import (
    PrecedentEmbeddingsProvider,
)
from animus.core.intake.interfaces.precedents_embeddings_repository import (
    PrecedentsEmbeddingsRepository,
)
from animus.core.intake.interfaces.precedents_repository import PrecedentsRepository
from animus.core.shared.responses.page_pagination_response import PagePaginationResponse


class VectorizePrecedentsUseCase:
    def __init__(
        self,
        pangea_service: PangeaService,
        precedents_repository: PrecedentsRepository,
        embeddings_provider: PrecedentEmbeddingsProvider,
        embeddings_repository: PrecedentsEmbeddingsRepository,
    ) -> None:
        self._precedents_repository = precedents_repository
        self._pangea_service = pangea_service
        self._embeddings_repository = embeddings_repository
        self._embeddings_provider = embeddings_provider

    def execute(self, page: int, page_size: int) -> PagePaginationResponse[Precedent]:
        pangea_page_response = self._pangea_service.fetch_precedents(page, page_size)
        existing_identifiers = self._precedents_repository.find_all_identifiers()
        new_precedents = [
            precedent
            for precedent in pangea_page_response.items
            if precedent.identifier not in existing_identifiers
        ]
        if new_precedents and len(new_precedents) > 0:
            self._precedents_repository.add_many(new_precedents)
            precedents_embbedings = self._embeddings_provider.generate(new_precedents)
            self._embeddings_repository.add_many(precedents_embbedings)
        return pangea_page_response
