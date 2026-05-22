import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.errors import ChosenAnalysisPrecedentsRequiredError
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.events import (
    SecondInstanceJudgmentDraftGenerationTriggeredEvent,
)
from animus.core.intake.use_cases import (
    CreateSecondInstanceJudgmentDraftUseCase,
    UpdateAnalysisStatusUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysesRepository,
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyCaseSummariesRepository,
    SqlalchemySecondInstanceJudgmentDraftsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pipes.ai_pipe import AiPipe
from animus.pubsub.inngest.inngest_job import InngestJob


@dataclass(frozen=True)
class _Payload:
    analysis_id: str


class GenerateSecondInstanceJudgmentDraftJob(InngestJob):
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='generate-judgment-draft',
            trigger=TriggerEvent(
                event=SecondInstanceJudgmentDraftGenerationTriggeredEvent.name,
            ),
            retries=2,
            on_failure=GenerateSecondInstanceJudgmentDraftJob._handle_failure,
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                GenerateSecondInstanceJudgmentDraftJob._normalize_payload,
                data,
            )
            payload = _Payload(analysis_id=str(normalized_data['analysis_id']))

            try:
                await context.step.run(
                    'mark_analysis_as_generating_judgment_draft',
                    lambda payload=payload: (
                        GenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_generating_judgment_draft(
                            payload
                        )
                    ),
                )

                await context.step.run(
                    'generate_and_persist_judgment_draft',
                    lambda payload=payload: (
                        GenerateSecondInstanceJudgmentDraftJob._generate_and_persist_judgment_draft(
                            payload
                        )
                    ),
                )
            except Exception:
                await context.step.run(
                    'mark_analysis_as_failed',
                    lambda payload=payload: (
                        GenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_failed(
                            payload
                        )
                    ),
                )
                raise

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {'analysis_id': str(data['analysis_id'])}

    @staticmethod
    async def _mark_analysis_as_generating_judgment_draft(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                GenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_generating_judgment_draft_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _mark_analysis_as_generating_judgment_draft_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            analysis_id = Id.create(payload.analysis_id)
            analysis = SqlalchemyAnalysesRepository(session).find_by_id(analysis_id)
            if analysis is None:
                return

            UpdateAnalysisStatusUseCase(SqlalchemyAnalysesRepository(session)).execute(
                analysis_id=analysis_id.value,
                status=SecondInstanceAnalysisStatus.create_as_generating_judgment_draft().dto,
            )
            session.commit()

    @staticmethod
    async def _generate_and_persist_judgment_draft(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                GenerateSecondInstanceJudgmentDraftJob._generate_and_persist_judgment_draft_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _generate_and_persist_judgment_draft_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            analyses_repository = SqlalchemyAnalysesRepository(session)
            case_summaries_repository = SqlalchemyCaseSummariesRepository(session)
            analysis_precedents_repository = SqlalchemyAnalysisPrecedentsRepository(
                session
            )
            judgment_drafts_repository = (
                SqlalchemySecondInstanceJudgmentDraftsRepository(session)
            )

            analysis_id = Id.create(payload.analysis_id)
            case_summary = case_summaries_repository.find_by_analysis_id(analysis_id)
            if case_summary is None:
                return

            precedents = analysis_precedents_repository.find_many_by_analysis_id(
                analysis_id=analysis_id
            )
            if len(precedents.items) == 0:
                raise ChosenAnalysisPrecedentsRequiredError

            chosen_precedents = [
                precedent
                for precedent in precedents.items
                if precedent.is_chosen.is_true
            ]
            if len(chosen_precedents) == 0:
                raise ChosenAnalysisPrecedentsRequiredError

            workflow = AiPipe.get_generate_judgment_draft_workflow()
            judgment_draft_dto = workflow.run(
                analysis_id=analysis_id.value,
                case_summary=case_summary,
                precedents=chosen_precedents,
            )

            CreateSecondInstanceJudgmentDraftUseCase(
                judgment_drafts_repository=judgment_drafts_repository,
                analyses_repository=analyses_repository,
            ).execute(
                analysis_id=analysis_id.value,
                dto=judgment_draft_dto,
            )
            session.commit()

    @staticmethod
    async def _mark_analysis_as_failed(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                GenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_failed_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _mark_analysis_as_failed_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            analysis_id = Id.create(payload.analysis_id)
            analysis = SqlalchemyAnalysesRepository(session).find_by_id(analysis_id)
            if analysis is None:
                return

            UpdateAnalysisStatusUseCase(SqlalchemyAnalysesRepository(session)).execute(
                analysis_id=analysis_id.value,
                status=SecondInstanceAnalysisStatus.create_as_failed().dto,
            )
            session.commit()

    @staticmethod
    async def _handle_failure(context: Context) -> None:
        event_data = (
            GenerateSecondInstanceJudgmentDraftJob.get_event_data_from_context_failure(
                context
            )
        )
        normalized_data = (
            await GenerateSecondInstanceJudgmentDraftJob._normalize_payload(event_data)
        )
        payload = _Payload(analysis_id=str(normalized_data['analysis_id']))

        await GenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_failed(payload)
