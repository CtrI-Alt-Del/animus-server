from typing import Any

from inngest import Context, Inngest, TriggerCron, TriggerEvent

from animus.core.intake.use_cases.vectorize_precedents_use_case import (
    VectorizePrecedentsUseCase,
)
from animus.database.qdrant.qdrant_precedents_embeddings_repository import (
    QdrantPrecedentsEmbeddingsRepository,
)
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_precendents_repository import (
    SqlalchemyPrecedentsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.intake.precedent_embeddings.gemini.gemini_precedent_embeddings_provider import (
    GeminiPrecedentEmbeddingsProvider,
)
from animus.rest.httpx.httpx_rest_client import HttpxRestClient
from animus.rest.pangea.services.pangea_bnp_service import PangeaBnpService


class VectorizePrecedentsJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='vectorize-precedents',
            trigger=[
                TriggerCron(cron='0 2 * * 1'),
                TriggerEvent(event='intake/vectorize-precedents.requested'),
            ],
        )
        async def _(context: Context) -> None:
            page = 1
            page_size = 100
            while True:
                has_next = await context.step.run(
                    f'vectorize-page-{page}',
                    lambda: _vectorize_precedents(page, page_size),  # noqa: B023
                )
                if not has_next:
                    break
                page += 1

        async def _vectorize_precedents(page: int, page_size: int) -> bool:
            with Sqlalchemy.session() as session:
                use_case = VectorizePrecedentsUseCase(
                    pangea_service=PangeaBnpService(client=HttpxRestClient()),
                    precedents_repository=SqlalchemyPrecedentsRepository(session),
                    embeddings_provider=GeminiPrecedentEmbeddingsProvider(),
                    embeddings_repository=QdrantPrecedentsEmbeddingsRepository(),
                )
                result = use_case.execute(page=page, page_size=page_size)
                return result.has_next_page

        return _
