from animus.core.intake.interfaces import (
    PrecedentEmbeddingsProvider,
    PrecedentsEmbeddingsRepository,
    PrecedentsRepository,
)


class VectorizeAllPrecedentsUseCase:
    def __init__(
        self,
        precedents_repository: PrecedentsRepository,
        precedent_embeddings_provider: PrecedentEmbeddingsProvider,
        precedents_embeddings_repository: PrecedentsEmbeddingsRepository,
    ) -> None:
        self._precedents_repository = precedents_repository
        self._precedent_embeddings_provider = precedent_embeddings_provider
        self._precedents_embeddings_repository = precedents_embeddings_repository

    def execute(self, page: int, page_size: int) -> int:
        precedents_page = self._precedents_repository.find_page(page, page_size)

        if not precedents_page.items:
            return 0

        embeddings = self._precedent_embeddings_provider.generate(precedents_page.items)
        self._precedents_embeddings_repository.add_many(embeddings)

        return len(precedents_page.items)
