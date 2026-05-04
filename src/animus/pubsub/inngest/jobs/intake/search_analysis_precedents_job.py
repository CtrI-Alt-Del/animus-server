import asyncio
from dataclasses import asdict, dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.events import (
    PrecedentsSearchFinishedEvent,
    AnalysisPrecedentsSearchRequestedEvent,
)
from animus.core.intake.domain.structures.dtos import AnalysisPrecedentDto
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.shared.domain.structures import Id
from animus.core.intake.use_cases import (
    SearchAnalysisPrecedentsUseCase,
    UpdateAnalysisStatusUseCase,
)
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalisysesRepository,
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyPetitionSummariesRepository,
    SqlalchemyPrecedentsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.intake.petition_summary_embeddings.openai.openai_petition_summary_embeddings_provider import (
    OpenAIPetitionSummaryEmbeddingsProvider,
)
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.inngest_job import InngestJob
from animus.database.qdrant.qdrant_precedents_embeddings_repository import (
    QdrantPrecedentsEmbeddingsRepository,
)


def _build_precedents_embeddings_repository() -> QdrantPrecedentsEmbeddingsRepository:
    return QdrantPrecedentsEmbeddingsRepository()


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    courts: list[str]
    precedent_kinds: list[str]
    limit: int

    @property
    def filters_dto(self) -> AnalysisPrecedentsSearchFiltersDto:
        return AnalysisPrecedentsSearchFiltersDto(
            courts=self.courts,
            precedent_kinds=self.precedent_kinds,
            limit=self.limit,
        )


@dataclass(frozen=True)
class _SearchPrecedentsResult:
    analysis_precedents_data: list[dict[str, Any]]
    account_id: str


class SearchAnalysisPrecedentsJob(InngestJob):
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='search-analysis-precedents',
            trigger=TriggerEvent(
                event=AnalysisPrecedentsSearchRequestedEvent.name,
            ),
            retries=2,
            on_failure=SearchAnalysisPrecedentsJob._handle_failure,
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                SearchAnalysisPrecedentsJob._normalize_payload,
                data,
            )
            payload = _Payload(
                analysis_id=str(normalized_data['analysis_id']),
                courts=list(normalized_data['courts']),
                precedent_kinds=list(normalized_data['precedent_kinds']),
                limit=int(normalized_data['limit']),
            )

            try:
                search_result_data = await context.step.run(
                    'search_precedents',
                    lambda payload=payload: (
                        SearchAnalysisPrecedentsJob._search_precedents(
                            payload,
                        )
                    ),
                )
                search_result = _SearchPrecedentsResult(
                    analysis_precedents_data=list(
                        search_result_data['analysis_precedents_data']
                    ),
                    account_id=str(search_result_data['account_id']),
                )

                await context.step.run(
                    'mark_analysis_as_analyzing_similarity',
                    lambda payload=payload: (
                        SearchAnalysisPrecedentsJob._mark_analysis_as_analyzing_similarity(
                            payload,
                        )
                    ),
                )

                await context.step.run(
                    'synthesize_analysis_precedents',
                    lambda payload=payload, analysis_precedents_data=search_result.analysis_precedents_data: (
                        SearchAnalysisPrecedentsJob._synthesize_analysis_precedents(
                            payload,
                            analysis_precedents_data,
                        )
                    ),
                )

                await context.step.run(
                    'publish_finished_event',
                    lambda payload=payload: InngestBroker(inngest).publish(  # type: ignore
                        PrecedentsSearchFinishedEvent(
                            analysis_id=payload.analysis_id,
                            account_id=search_result.account_id,
                        )
                    ),
                )
            except Exception:
                await context.step.run(
                    'mark_analysis_as_failed',
                    lambda payload=payload: (
                        SearchAnalysisPrecedentsJob._mark_analysis_as_failed(
                            payload,
                        )
                    ),
                )
                raise

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
        return {
            'analysis_id': str(data['analysis_id']),
            'courts': [str(court) for court in list(data.get('courts', []))],
            'precedent_kinds': [
                str(precedent_kind)
                for precedent_kind in list(data.get('precedent_kinds', []))
            ],
            'limit': int(data['limit']),
        }

    @staticmethod
    async def _search_precedents(
        payload: _Payload,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: SearchAnalysisPrecedentsJob._search_precedents_sync(payload),
        )

    @staticmethod
    def _search_precedents_sync(
        payload: _Payload,
    ) -> dict[str, Any]:
        with Sqlalchemy.session() as session:
            analisyses_repository = SqlalchemyAnalisysesRepository(session)
            petition_summaries_repository = SqlalchemyPetitionSummariesRepository(
                session
            )
            precedents_repository = SqlalchemyPrecedentsRepository(session)
            UpdateAnalysisStatusUseCase(analisyses_repository).execute(
                analysis_id=payload.analysis_id,
                status=AnalysisStatusValue.SEARCHING_PRECEDENTS.value,
            )
            session.commit()

            analysis = analisyses_repository.find_by_id(Id.create(payload.analysis_id))
            if analysis is None:
                return {
                    'analysis_precedents_data': [],
                    'account_id': '',
                }

            analysis_precedents = SearchAnalysisPrecedentsUseCase(
                petition_summaries_repository=petition_summaries_repository,
                petition_summary_embeddings_provider=(
                    OpenAIPetitionSummaryEmbeddingsProvider()
                ),
                precedents_embeddings_repository=(
                    _build_precedents_embeddings_repository()
                ),
                precedents_repository=precedents_repository,
            ).execute(
                analysis_id=payload.analysis_id,
                dto=payload.filters_dto,
            )

        return {
            'analysis_precedents_data': [
                asdict(analysis_precedent) for analysis_precedent in analysis_precedents
            ],
            'account_id': analysis.account_id.value,
        }

    @staticmethod
    async def _mark_analysis_as_analyzing_similarity(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                SearchAnalysisPrecedentsJob._mark_analysis_as_analyzing_similarity_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _mark_analysis_as_analyzing_similarity_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            UpdateAnalysisStatusUseCase(
                SqlalchemyAnalisysesRepository(session)
            ).execute(
                analysis_id=payload.analysis_id,
                status=AnalysisStatusValue.ANALYZING_PRECEDENTS_SIMILARITY.value,
            )
            session.commit()

    @staticmethod
    async def _synthesize_analysis_precedents(
        payload: _Payload,
        analysis_precedents_data: list[dict[str, Any]],
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: SearchAnalysisPrecedentsJob._synthesize_analysis_precedents_sync(
                payload,
                analysis_precedents_data,
            ),
        )

    @staticmethod
    def _synthesize_analysis_precedents_sync(
        payload: _Payload,
        analysis_precedents_data: list[dict[str, Any]],
    ) -> None:
        from animus.pipes.ai_pipe import AiPipe

        with Sqlalchemy.session() as session:
            analisyses_repository = SqlalchemyAnalisysesRepository(session)
            petition_summaries_repository = SqlalchemyPetitionSummariesRepository(
                session
            )
            analysis_precedents_repository = SqlalchemyAnalysisPrecedentsRepository(
                session
            )

            UpdateAnalysisStatusUseCase(analisyses_repository).execute(
                analysis_id=payload.analysis_id,
                status=AnalysisStatusValue.GENERATING_SYNTHESIS.value,
            )
            session.commit()

            workflow = AiPipe.get_synthesize_analysis_precedents_workflow(
                petition_summaries_repository=petition_summaries_repository,
                analysis_precedents_repository=analysis_precedents_repository,
                analisyses_repository=analisyses_repository,
            )

            workflow.run(
                analysis_id=payload.analysis_id,
                filters_dto=payload.filters_dto,
                analysis_precedents=[
                    AnalysisPrecedentDto(**analysis_precedent_data)
                    for analysis_precedent_data in analysis_precedents_data
                ],
            )
            session.commit()

    @staticmethod
    async def _mark_analysis_as_failed(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        print('SearchAnalysisPrecedentsJob._mark_analysis_as_failed')
        await loop.run_in_executor(
            None,
            lambda: SearchAnalysisPrecedentsJob._mark_analysis_as_failed_sync(payload),
        )

    @staticmethod
    def _mark_analysis_as_failed_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            UpdateAnalysisStatusUseCase(
                SqlalchemyAnalisysesRepository(session)
            ).execute(
                analysis_id=payload.analysis_id,
                status=AnalysisStatusValue.FAILED.value,
            )
            session.commit()

    @staticmethod
    async def _handle_failure(context: Context) -> None:
        event_data = SearchAnalysisPrecedentsJob.get_event_data_from_context_failure(
            context
        )
        normalized_data = await SearchAnalysisPrecedentsJob._normalize_payload(
            event_data
        )
        payload = _Payload(
            analysis_id=str(normalized_data['analysis_id']),
            courts=list(normalized_data['courts']),
            precedent_kinds=list(normalized_data['precedent_kinds']),
            limit=int(normalized_data['limit']),
        )
        await SearchAnalysisPrecedentsJob._mark_analysis_as_failed(payload)
