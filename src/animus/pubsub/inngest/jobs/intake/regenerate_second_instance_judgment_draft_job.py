import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    DraftRegenerationCaseSummaryUnavailableError,
    DraftRegenerationChosenPrecedentsRequiredError,
    SecondInstanceDecisionNotFoundError,
    SecondInstanceJudgmentDraftRegenerationUnavailableError,
)
from animus.core.intake.domain.events import (
    SecondInstanceJudgmentDraftGenerationFinishedEvent,
    SecondInstanceJudgmentDraftRegenerationTriggeredEvent,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
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
    SqlalchemySecondInstanceDecisionsRepository,
    SqlalchemySecondInstanceJudgmentDraftsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pipes.ai_pipe import AiPipe
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.inngest_job import InngestJob


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    comments: str


@dataclass(frozen=True)
class _GenerationResult:
    analysis_id: str
    account_id: str
    analysis_type: str


class RegenerateSecondInstanceJudgmentDraftJob(InngestJob):
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='regenerate-second-instance-judgment-draft',
            trigger=TriggerEvent(
                event=SecondInstanceJudgmentDraftRegenerationTriggeredEvent.name,
            ),
            retries=2,
            on_failure=RegenerateSecondInstanceJudgmentDraftJob._handle_failure,
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                RegenerateSecondInstanceJudgmentDraftJob._normalize_payload,
                data,
            )
            payload = _Payload(
                analysis_id=str(normalized_data['analysis_id']),
                comments=str(normalized_data['comments']),
            )

            try:
                await context.step.run(
                    'mark_analysis_as_regenerating_judgment_draft',
                    lambda payload=payload: (
                        RegenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_regenerating_judgment_draft(
                            payload
                        )
                    ),
                )

                generation_result_data = await context.step.run(
                    'regenerate_and_persist_judgment_draft',
                    lambda payload=payload: (
                        RegenerateSecondInstanceJudgmentDraftJob._regenerate_and_persist_judgment_draft(
                            payload
                        )
                    ),
                )

                generation_result = _GenerationResult(
                    analysis_id=str(generation_result_data['analysis_id']),
                    account_id=str(generation_result_data['account_id']),
                    analysis_type=str(generation_result_data['analysis_type']),
                )

                await context.step.run(
                    'publish_finished_event',
                    lambda: InngestBroker(inngest).publish(  # type: ignore
                        SecondInstanceJudgmentDraftGenerationFinishedEvent(
                            analysis_id=generation_result.analysis_id,
                            account_id=generation_result.account_id,
                            analysis_type=generation_result.analysis_type,
                        )
                    ),
                )
            except Exception:
                await context.step.run(
                    'mark_analysis_as_failed',
                    lambda payload=payload: (
                        RegenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_failed(
                            payload
                        )
                    ),
                )
                raise

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {
            'analysis_id': str(data['analysis_id']).strip(),
            'comments': str(data['comments']).strip(),
        }

    @staticmethod
    async def _mark_analysis_as_regenerating_judgment_draft(
        payload: _Payload,
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                RegenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_regenerating_judgment_draft_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _mark_analysis_as_regenerating_judgment_draft_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            analyses_repository = SqlalchemyAnalysesRepository(session)
            analysis_id = Id.create(payload.analysis_id)
            analysis = analyses_repository.find_by_id(analysis_id)
            if analysis is None:
                return

            UpdateAnalysisStatusUseCase(analyses_repository).execute(
                analysis_id=analysis_id.value,
                status=SecondInstanceAnalysisStatus.create_as_generating_judgment_draft().dto,
            )
            session.commit()

    @staticmethod
    async def _regenerate_and_persist_judgment_draft(
        payload: _Payload,
    ) -> dict[str, str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: (
                RegenerateSecondInstanceJudgmentDraftJob._regenerate_and_persist_judgment_draft_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _regenerate_and_persist_judgment_draft_sync(
        payload: _Payload,
    ) -> dict[str, str]:
        with Sqlalchemy.session() as session:
            analyses_repository = SqlalchemyAnalysesRepository(session)
            case_summaries_repository = SqlalchemyCaseSummariesRepository(session)
            analysis_precedents_repository = SqlalchemyAnalysisPrecedentsRepository(
                session
            )
            second_instance_decisions_repository = (
                SqlalchemySecondInstanceDecisionsRepository(session)
            )
            judgment_drafts_repository = (
                SqlalchemySecondInstanceJudgmentDraftsRepository(session)
            )

            analysis_id = Id.create(payload.analysis_id)
            analysis = analyses_repository.find_by_id(analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError

            current_draft = judgment_drafts_repository.find_by_analysis_id(analysis_id)
            if current_draft is None:
                raise SecondInstanceJudgmentDraftRegenerationUnavailableError

            case_summary = case_summaries_repository.find_by_analysis_id(analysis_id)
            if case_summary is None:
                raise DraftRegenerationCaseSummaryUnavailableError

            second_instance_decision = (
                second_instance_decisions_repository.find_by_analysis_id(analysis_id)
            )
            if second_instance_decision is None:
                raise SecondInstanceDecisionNotFoundError

            precedents = analysis_precedents_repository.find_many_by_analysis_id(
                analysis_id=analysis_id
            )
            chosen_precedents = [
                precedent
                for precedent in precedents.items
                if precedent.is_chosen.is_true
            ]
            if len(chosen_precedents) == 0:
                raise DraftRegenerationChosenPrecedentsRequiredError

            judgment_draft_dto = AiPipe.get_regenerate_judgment_draft_workflow().run(
                analysis_id=analysis_id.value,
                current_draft=current_draft,
                case_summary=case_summary,
                precedents=chosen_precedents,
                comments=payload.comments,
                second_instance_decision=second_instance_decision,
            )

            CreateSecondInstanceJudgmentDraftUseCase(
                judgment_drafts_repository=judgment_drafts_repository,
                analyses_repository=analyses_repository,
            ).execute(
                analysis_id=analysis_id.value,
                dto=judgment_draft_dto,
            )
            session.commit()

            return {
                'analysis_id': analysis_id.value,
                'account_id': analysis.account_id.value,
                'analysis_type': analysis.type.dto,
            }

    @staticmethod
    async def _mark_analysis_as_failed(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                RegenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_failed_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _mark_analysis_as_failed_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            analyses_repository = SqlalchemyAnalysesRepository(session)
            analysis_id = Id.create(payload.analysis_id)
            analysis = analyses_repository.find_by_id(analysis_id)
            if analysis is None:
                return

            UpdateAnalysisStatusUseCase(analyses_repository).execute(
                analysis_id=analysis_id.value,
                status=SecondInstanceAnalysisStatus.create_as_failed().dto,
            )
            session.commit()

    @staticmethod
    async def _handle_failure(context: Context) -> None:
        event_data = RegenerateSecondInstanceJudgmentDraftJob.get_event_data_from_context_failure(
            context
        )
        normalized_data = (
            await RegenerateSecondInstanceJudgmentDraftJob._normalize_payload(
                event_data
            )
        )
        payload = _Payload(
            analysis_id=str(normalized_data['analysis_id']),
            comments=str(normalized_data['comments']),
        )

        await RegenerateSecondInstanceJudgmentDraftJob._mark_analysis_as_failed(payload)
