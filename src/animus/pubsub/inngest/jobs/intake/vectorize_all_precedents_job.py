import asyncio
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.use_cases.vectorize_all_precedents_use_case import (
    VectorizeAllPrecedentsUseCase,
)
from animus.database.qdrant.qdrant_precedents_embeddings_repository import (
    QdrantPrecedentsEmbeddingsRepository,
)
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyPrecedentsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.intake.precedent_embeddings.openai.openai_precedent_embeddings_provider import (
    OpenAIPrecedentEmbeddingsProvider,
)


class VectorizeAllPrecedentsJob:
    _PAGE_SIZE = 100

    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='vectorize-all-precedents',
            trigger=TriggerEvent(event='intake/vectorize-all-precedents.requested'),
        )
        async def _(context: Context) -> None:
            page = 1

            while True:
                vectorized_count = await context.step.run(
                    f'vectorize-all-precedents-page-{page}',
                    lambda page=page: VectorizeAllPrecedentsJob._vectorize_page(page),
                )

                if vectorized_count < VectorizeAllPrecedentsJob._PAGE_SIZE:
                    break

                page += 1

        return _

    @staticmethod
    async def _vectorize_page(page: int) -> int:
        with Sqlalchemy.session() as session:
            use_case = VectorizeAllPrecedentsUseCase(
                precedents_repository=SqlalchemyPrecedentsRepository(session),
                precedent_embeddings_provider=OpenAIPrecedentEmbeddingsProvider(),
                precedents_embeddings_repository=QdrantPrecedentsEmbeddingsRepository(),
            )
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                lambda: use_case.execute(
                    page=page,
                    page_size=VectorizeAllPrecedentsJob._PAGE_SIZE,
                ),
            )
