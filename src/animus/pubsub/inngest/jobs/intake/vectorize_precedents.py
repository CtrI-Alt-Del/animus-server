from typing import Any

from inngest import Context, Inngest, TriggerCron

from animus.core.intake.use_cases.vectorize_precedents_use_case import (
    VectorizePrecedentsUseCase,
)
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_precendents_repository import SqlalchemyPrecedentsRepository
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.database.vertex_ai.vertex_ai_precedents_embeddings_repository import VertexAiPrecedentsEmbeddingsRepository
from animus.providers.intake.precedent_embeddings.gemini.gemini_precedent_embeddings_provider import GeminiPrecedentEmbeddingsProvider
from animus.rest.httpx.httpx_rest_client import HttpxRestClient
from animus.rest.pangea.services.pangea_bnp_service import PangeaBnpService


class VectorizePrecedentsJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='vectorize-precedents', trigger=TriggerCron(cron='0 2 * * 1')
        )
        async def _(context: Context) -> None:
            page = 1
            page_size = 100
            while True:
                has_next = await context.step.run(
                    f'vectorize-page-{page}',
                    lambda: _vectorize_precedents(page, page_size),
                )
                if not has_next:
                    break
                page += 1

        async def _vectorize_precedents(page: int, page_size: int) -> bool:
            #@TODO: todo no pangeabnp service
            #@TODO: talvez error no embedding_provider
            with Sqlalchemy.session() as session:
                use_case = VectorizePrecedentsUseCase(
                    pangea_service=PangeaBnpService(client=HttpxRestClient()),
                    precedents_repository=SqlalchemyPrecedentsRepository(session),
                    embeddings_provider=GeminiPrecedentEmbeddingsProvider(),
                    embeddings_repository=VertexAiPrecedentsEmbeddingsRepository(),
                )
                result = use_case.execute(page=page, page_size=page_size)
                return result.has_next_page
