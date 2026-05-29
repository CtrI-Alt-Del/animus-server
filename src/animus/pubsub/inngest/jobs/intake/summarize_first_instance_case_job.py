import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.ai.agno.workflows.intake.agno_summarize_first_instance_case_workflow import (
    AgnoSummarizeFirstInstanceCaseWorkflow,
)
from animus.core.intake.domain.errors.analysis_document_not_found_error import (
    AnalysisDocumentNotFoundError,
)
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.domain.events import (
    CaseSummaryFinishedEvent,
)
from animus.core.intake.domain.events.first_instance_summarization_triggered_event import (
    FistInstanceCaseSummarizationTriggeredEvent,
)
from animus.core.intake.use_cases import UpdateAnalysisStatusUseCase
from animus.core.shared.domain.structures import Id
from animus.core.storage.use_cases import GetDocumentContentUseCase
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysisDocumentsRepository,
    SqlalchemyAnalysesRepository,
    SqlalchemyCaseSummariesRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.storage import (
    GcsFileStorageProvider,
    PypdfPdfProvider,
    PythonDocxProvider,
)
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.inngest_job import InngestJob


@dataclass(frozen=True)
class _Payload:
    analysis_id: str


@dataclass(frozen=True)
class _SummaryResult:
    analysis_id: str
    account_id: str
    analysis_type: str


class SummarizeFirstInstanceCaseJob(InngestJob):
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='summarize-first-instance-case',
            trigger=TriggerEvent(
                event=FistInstanceCaseSummarizationTriggeredEvent.name
            ),
            retries=0,
            on_failure=SummarizeFirstInstanceCaseJob._handle_failure,
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                SummarizeFirstInstanceCaseJob._normalize_payload,
                data,
            )
            payload = _Payload(analysis_id=str(normalized_data['analysis_id']))

            try:
                summary_result_data = await context.step.run(
                    'summarize_case',
                    lambda payload=payload: (
                        SummarizeFirstInstanceCaseJob._summarize_case(payload)
                    ),
                )
                summary_result = _SummaryResult(
                    analysis_id=str(summary_result_data['analysis_id']),
                    account_id=str(summary_result_data['account_id']),
                    analysis_type=str(summary_result_data['analysis_type']),
                )

                await context.step.run(
                    'publish_finished_event',
                    lambda: InngestBroker(inngest).publish(  # type:ignore
                        CaseSummaryFinishedEvent(
                            analysis_id=summary_result.analysis_id,
                            account_id=summary_result.account_id,
                            analysis_type=summary_result.analysis_type,
                        )
                    ),
                )
            except Exception:
                await context.step.run(
                    'mark_analysis_as_failed',
                    lambda payload=payload: (
                        SummarizeFirstInstanceCaseJob._mark_analysis_as_failed(payload)
                    ),
                )
                raise

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {'analysis_id': str(data['analysis_id'])}

    @staticmethod
    async def _summarize_case(payload: _Payload) -> dict[str, str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: SummarizeFirstInstanceCaseJob._summarize_case_sync(payload),
        )

    @staticmethod
    def _summarize_case_sync(payload: _Payload) -> dict[str, str]:
        with Sqlalchemy.session() as session:
            analysis_documents_repository = SqlalchemyAnalysisDocumentsRepository(
                session
            )
            case_summaries_repository = SqlalchemyCaseSummariesRepository(session)
            analyses_repository = SqlalchemyAnalysesRepository(session)

            analysis_id = Id.create(payload.analysis_id)
            analysis_document = analysis_documents_repository.find_by_analysis_id(
                analysis_id
            )
            if analysis_document is None:
                raise AnalysisDocumentNotFoundError

            analysis = analyses_repository.find_by_id(analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError

            document_content = GetDocumentContentUseCase(
                file_storage_provider=GcsFileStorageProvider(),
                pdf_provider=PypdfPdfProvider(),
                docx_provider=PythonDocxProvider(),
            ).execute(file_path=analysis_document.file_path)

            workflow = AgnoSummarizeFirstInstanceCaseWorkflow(
                case_summaries_repository=case_summaries_repository,
                analysis_documents_repository=analysis_documents_repository,
                analyses_repository=analyses_repository,
            )
            workflow.run(
                analysis_id=analysis_id.value,
                document_content=document_content,
            )

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
            lambda: SummarizeFirstInstanceCaseJob._mark_analysis_as_failed_sync(
                payload
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
                status='FAILED',
            )
            session.commit()

    @staticmethod
    async def _handle_failure(context: Context) -> None:
        event_data = SummarizeFirstInstanceCaseJob.get_event_data_from_context_failure(
            context
        )
        normalized_data = await SummarizeFirstInstanceCaseJob._normalize_payload(
            event_data
        )
        payload = _Payload(analysis_id=str(normalized_data['analysis_id']))

        await SummarizeFirstInstanceCaseJob._mark_analysis_as_failed(payload)
