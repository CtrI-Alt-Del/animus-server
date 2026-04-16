import asyncio
from dataclasses import asdict, dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PetitionSummaryUnavailableError,
)
from animus.core.intake.domain.events import (
    AnalysisPrecedentsSearchRequestedEvent,
)
from animus.core.intake.domain.structures.dtos import AnalysisPrecedentDto
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.use_cases import (
    SearchAnalysisPrecedentsUseCase,
    UpdateAnalysisStatusUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.database.qdrant.qdrant_precedents_embeddings_repository import (
    QdrantPrecedentsEmbeddingsRepository,
)
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyAnalisysesRepository,
    SqlalchemyPetitionSummariesRepository,
    SqlalchemyPrecedentsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.intake.petition_summary_embeddings.openai.openai_petition_summary_embeddings_provider import (
    OpenAIPetitionSummaryEmbeddingsProvider,
)


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


class SearchAnalysisPrecedentsJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='search-analysis-precedents',
            trigger=TriggerEvent(
                event=AnalysisPrecedentsSearchRequestedEvent.name,
            ),
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
                analysis_precedents_data = await context.step.run(
                    'search_precedents',
                    lambda payload=payload: (
                        SearchAnalysisPrecedentsJob._search_precedents(
                            payload,
                        )
                    ),
                )

                await context.step.run(
                    'generate_syntheses_and_persist',
                    lambda payload=payload, analysis_precedents_data=analysis_precedents_data: (
                        SearchAnalysisPrecedentsJob._generate_syntheses_and_persist(
                            payload,
                            analysis_precedents_data,
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
    ) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: SearchAnalysisPrecedentsJob._search_precedents_sync(payload),
        )

    @staticmethod
    def _search_precedents_sync(
        payload: _Payload,
    ) -> list[dict[str, Any]]:
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

            analysis_precedents = SearchAnalysisPrecedentsUseCase(
                petition_summaries_repository=petition_summaries_repository,
                petition_summary_embeddings_provider=(
                    OpenAIPetitionSummaryEmbeddingsProvider()
                ),
                precedents_embeddings_repository=QdrantPrecedentsEmbeddingsRepository(),
                precedents_repository=precedents_repository,
            ).execute(
                analysis_id=payload.analysis_id,
                dto=payload.filters_dto,
            )

        return [
            asdict(analysis_precedent) for analysis_precedent in analysis_precedents
        ]

    @staticmethod
    async def _generate_syntheses_and_persist(
        payload: _Payload,
        analysis_precedents_data: list[dict[str, Any]],
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: SearchAnalysisPrecedentsJob._generate_syntheses_and_persist_sync(
                payload,
                analysis_precedents_data,
            ),
        )

    @staticmethod
    def _generate_syntheses_and_persist_sync(
        payload: _Payload,
        analysis_precedents_data: list[dict[str, Any]],
    ) -> None:
        with Sqlalchemy.session() as session:
            analisyses_repository = SqlalchemyAnalisysesRepository(session)
            petition_summaries_repository = SqlalchemyPetitionSummariesRepository(
                session
            )
            analysis_precedents_repository = SqlalchemyAnalysisPrecedentsRepository(
                session
            )
            analysis_id = Id.create(payload.analysis_id)

            UpdateAnalysisStatusUseCase(analisyses_repository).execute(
                analysis_id=payload.analysis_id,
                status=AnalysisStatusValue.GENERATING_SYNTHESIS.value,
            )
            session.commit()

            petition_summary = petition_summaries_repository.find_by_analysis_id(
                analysis_id=analysis_id,
            )
            if petition_summary is None:
                raise PetitionSummaryUnavailableError

            from animus.pipes.ai_pipe import AiPipe

            workflow = AiPipe.get_synthesize_analysis_precedents_workflow()
            analysis_precedents = workflow.run(
                petition_summary=petition_summary,
                analysis_precedents=[
                    AnalysisPrecedentDto(**analysis_precedent_data)
                    for analysis_precedent_data in analysis_precedents_data
                ],
            )

            analysis_precedents_repository.remove_many_by_analysis_id(analysis_id)
            analysis_precedents_repository.add_many_by_analysis_id(
                analysis_id=analysis_id,
                analysis_precedents=analysis_precedents.items,
            )

            analysis = analisyses_repository.find_by_id(analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError

            analysis.set_precedents_search_filters(payload.filters_dto)
            analysis.set_status(AnalysisStatusValue.WAITING_PRECEDENT_CHOISE.value)
            analisyses_repository.replace(analysis)
            session.commit()

    @staticmethod
    async def _mark_analysis_as_failed(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
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
