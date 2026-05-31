import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    DraftRegenerationCaseSummaryUnavailableError,
    DraftRegenerationChosenPrecedentsRequiredError,
    PetitionDraftRegenerationUnavailableError,
)
from animus.core.intake.domain.events import (
    PetitionDraftGenerationFinishedEvent,
    PetitionDraftRegenerationTriggeredEvent,
)
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.use_cases import (
    CreatePetitionDraftUseCase,
    UpdateAnalysisStatusUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysesRepository,
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyCaseSummariesRepository,
    SqlalchemyPetitionDraftsRepository,
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


class RegeneratePetitionDraftJob(InngestJob):
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='regenerate-petition-draft',
            trigger=TriggerEvent(event=PetitionDraftRegenerationTriggeredEvent.name),
            retries=2,
            on_failure=RegeneratePetitionDraftJob._handle_failure,
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                RegeneratePetitionDraftJob._normalize_payload,
                data,
            )
            payload = _Payload(
                analysis_id=str(normalized_data['analysis_id']),
                comments=str(normalized_data['comments']),
            )

            try:
                await context.step.run(
                    'mark_analysis_as_regenerating_petition_draft',
                    lambda payload=payload: (
                        RegeneratePetitionDraftJob._mark_analysis_as_regenerating_petition_draft(
                            payload
                        )
                    ),
                )

                generation_result_data = await context.step.run(
                    'regenerate_and_persist_petition_draft',
                    lambda payload=payload: (
                        RegeneratePetitionDraftJob._regenerate_and_persist_petition_draft(
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
                        PetitionDraftGenerationFinishedEvent(
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
                        RegeneratePetitionDraftJob._mark_analysis_as_failed(payload)
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
    async def _mark_analysis_as_regenerating_petition_draft(
        payload: _Payload,
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                RegeneratePetitionDraftJob._mark_analysis_as_regenerating_petition_draft_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _mark_analysis_as_regenerating_petition_draft_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            analyses_repository = SqlalchemyAnalysesRepository(session)
            analysis_id = Id.create(payload.analysis_id)
            analysis = analyses_repository.find_by_id(analysis_id)
            if analysis is None:
                return

            UpdateAnalysisStatusUseCase(analyses_repository).execute(
                analysis_id=analysis_id.value,
                status=CaseAssessmentAnalysisStatus.create_as_generating_petition_draft().dto,
            )
            session.commit()

    @staticmethod
    async def _regenerate_and_persist_petition_draft(
        payload: _Payload,
    ) -> dict[str, str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: (
                RegeneratePetitionDraftJob._regenerate_and_persist_petition_draft_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _regenerate_and_persist_petition_draft_sync(
        payload: _Payload,
    ) -> dict[str, str]:
        with Sqlalchemy.session() as session:
            analyses_repository = SqlalchemyAnalysesRepository(session)
            case_summaries_repository = SqlalchemyCaseSummariesRepository(session)
            analysis_precedents_repository = SqlalchemyAnalysisPrecedentsRepository(
                session
            )
            petition_drafts_repository = SqlalchemyPetitionDraftsRepository(session)

            analysis_id = Id.create(payload.analysis_id)
            analysis = analyses_repository.find_by_id(analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError

            current_draft = petition_drafts_repository.find_by_analysis_id(analysis_id)
            if current_draft is None:
                raise PetitionDraftRegenerationUnavailableError

            case_summary = case_summaries_repository.find_by_analysis_id(analysis_id)
            if case_summary is None:
                raise DraftRegenerationCaseSummaryUnavailableError

            precedents = analysis_precedents_repository.find_many_by_analysis_id(
                analysis_id=analysis_id,
            )
            chosen_precedents = [
                precedent
                for precedent in precedents.items
                if precedent.is_chosen.is_true
            ]
            if len(chosen_precedents) == 0:
                raise DraftRegenerationChosenPrecedentsRequiredError

            petition_draft_dto = AiPipe.get_regenerate_petition_draft_workflow().run(
                analysis_id=analysis_id.value,
                current_draft=current_draft,
                case_summary=case_summary,
                precedents=chosen_precedents,
                comments=payload.comments,
            )

            CreatePetitionDraftUseCase(
                petition_drafts_repository=petition_drafts_repository,
                analyses_repository=analyses_repository,
            ).execute(
                analysis_id=analysis_id.value,
                dto=petition_draft_dto,
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
            lambda: RegeneratePetitionDraftJob._mark_analysis_as_failed_sync(payload),
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
                status=CaseAssessmentAnalysisStatus.create_as_failed().dto,
            )
            session.commit()

    @staticmethod
    async def _handle_failure(context: Context) -> None:
        event_data = RegeneratePetitionDraftJob.get_event_data_from_context_failure(
            context
        )
        normalized_data = await RegeneratePetitionDraftJob._normalize_payload(
            event_data
        )
        payload = _Payload(
            analysis_id=str(normalized_data['analysis_id']),
            comments=str(normalized_data['comments']),
        )

        await RegeneratePetitionDraftJob._mark_analysis_as_failed(payload)
