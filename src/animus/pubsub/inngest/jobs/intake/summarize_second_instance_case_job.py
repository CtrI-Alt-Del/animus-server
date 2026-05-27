import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.ai.agno.workflows.intake import (
    AgnoSummarizeSecondInstanceCaseWorkflow,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.errors import (
    AnalysisDocumentNotFoundError,
    AnalysisNotFoundError,
)
from animus.core.intake.domain.events import (
    CaseSummaryFinishedEvent,
    SecondInstanceCaseSummarizationTriggeredEvent,
)
from animus.core.intake.use_cases import UpdateAnalysisStatusUseCase
from animus.core.shared.domain.structures import Id, Text
from animus.core.storage.domain.errors import (
    CourtDocumentIndexNotFoundError,
    InsufficientCourtDocumentError,
)
from animus.core.storage.domain.structures import ExtractedCourtDocumentPieces
from animus.core.storage.use_cases import ExtractCourtDocumentPiecesUseCase
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysisDocumentsRepository,
    SqlalchemyAnalysesRepository,
    SqlalchemyCaseSummariesRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.storage import GcsFileStorageProvider, PypdfPdfProvider
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.inngest_job import InngestJob


@dataclass(frozen=True)
class _Payload:
    analysis_id: str


@dataclass(frozen=True)
class _SummaryResult:
    analysis_id: str
    account_id: str


class SummarizeSecondInstanceCaseJob(InngestJob):
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='summarize-second-instance-case',
            trigger=TriggerEvent(
                event=SecondInstanceCaseSummarizationTriggeredEvent.name
            ),
            retries=0,
            on_failure=SummarizeSecondInstanceCaseJob._handle_failure,
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                SummarizeSecondInstanceCaseJob._normalize_payload,
                data,
            )
            payload = _Payload(analysis_id=str(normalized_data['analysis_id']))

            try:
                summary_result_data = await context.step.run(
                    'extract_and_summarize',
                    lambda payload=payload: (
                        SummarizeSecondInstanceCaseJob._extract_and_summarize_case(
                            payload
                        )
                    ),
                )
                summary_result = _SummaryResult(
                    analysis_id=str(summary_result_data['analysis_id']),
                    account_id=str(summary_result_data['account_id']),
                )

                await context.step.run(
                    'publish_finished_event',
                    lambda: InngestBroker(inngest).publish(  # type: ignore
                        CaseSummaryFinishedEvent(
                            analysis_id=summary_result.analysis_id,
                            account_id=summary_result.account_id,
                        )
                    ),
                )
            except (
                CourtDocumentIndexNotFoundError,
                InsufficientCourtDocumentError,
            ):
                await context.step.run(
                    'mark_court_document_pieces_as_not_found',
                    lambda payload=payload: (
                        SummarizeSecondInstanceCaseJob._mark_court_document_pieces_as_not_found(
                            payload
                        )
                    ),
                )
            except Exception:
                await context.step.run(
                    'mark_analysis_as_failed',
                    lambda payload=payload: (
                        SummarizeSecondInstanceCaseJob._mark_analysis_as_failed(payload)
                    ),
                )
                raise

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {'analysis_id': str(data['analysis_id'])}

    @staticmethod
    async def _extract_and_summarize_case(payload: _Payload) -> dict[str, str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: SummarizeSecondInstanceCaseJob._extract_and_summarize_case_sync(
                payload
            ),
        )

    @staticmethod
    def _extract_and_summarize_case_sync(payload: _Payload) -> dict[str, str]:
        with Sqlalchemy.session() as session:
            analysis_documents_repository = SqlalchemyAnalysisDocumentsRepository(
                session
            )
            case_summaries_repository = SqlalchemyCaseSummariesRepository(session)
            analyses_repository = SqlalchemyAnalysesRepository(session)
            pdf_provider = PypdfPdfProvider()

            analysis_id = Id.create(payload.analysis_id)
            analysis_document = analysis_documents_repository.find_by_analysis_id(
                analysis_id
            )
            if analysis_document is None:
                raise AnalysisDocumentNotFoundError

            pdf_file = GcsFileStorageProvider().get_file(analysis_document.file_path)
            extracted_court_document_pieces = ExtractCourtDocumentPiecesUseCase(
                pdf_provider
            ).execute(
                pdf_file=pdf_file.dto,
            )
            document_content = SummarizeSecondInstanceCaseJob._build_document_content(
                extracted_court_document_pieces
            )

            UpdateAnalysisStatusUseCase(analyses_repository).execute(
                analysis_id=analysis_id.value,
                status=SecondInstanceAnalysisStatus.create_as_analyzing_case().dto,
            )
            session.commit()

            AgnoSummarizeSecondInstanceCaseWorkflow(
                case_summaries_repository=case_summaries_repository,
                analysis_documents_repository=analysis_documents_repository,
                analyses_repository=analyses_repository,
            ).run(
                analysis_id=analysis_id.value,
                document_content=document_content,
            )
            session.commit()

            analysis = analyses_repository.find_by_id(analysis_id)
            if analysis is None:
                raise AnalysisNotFoundError

            return {
                'analysis_id': analysis_id.value,
                'account_id': analysis.account_id.value,
            }

    @staticmethod
    def _build_document_content(
        extracted_court_document_pieces: ExtractedCourtDocumentPieces,
    ) -> Text:
        parts = [
            (
                'sentenca',
                extracted_court_document_pieces.sentenca.value,
            ),
            (
                'apelacao',
                extracted_court_document_pieces.apelacao.value,
            ),
        ]

        if extracted_court_document_pieces.contrarrazoes is not None:
            parts.append(
                (
                    'contrarrazoes',
                    extracted_court_document_pieces.contrarrazoes.value,
                )
            )

        return Text.create(
            '\n\n'.join(f'{header}:\n{content}' for header, content in parts)
        )

    @staticmethod
    async def _mark_court_document_pieces_as_not_found(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                SummarizeSecondInstanceCaseJob._mark_court_document_pieces_as_not_found_sync(
                    payload
                )
            ),
        )

    @staticmethod
    def _mark_court_document_pieces_as_not_found_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            analysis_id = Id.create(payload.analysis_id)
            analysis = SqlalchemyAnalysesRepository(session).find_by_id(analysis_id)
            if analysis is None:
                return

            UpdateAnalysisStatusUseCase(SqlalchemyAnalysesRepository(session)).execute(
                analysis_id=analysis_id.value,
                status=SecondInstanceAnalysisStatus.create_as_court_document_pieces_not_found().dto,
            )
            session.commit()

    @staticmethod
    async def _mark_analysis_as_failed(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: SummarizeSecondInstanceCaseJob._mark_analysis_as_failed_sync(
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
                status=SecondInstanceAnalysisStatus.create_as_failed().dto,
            )
            session.commit()

    @staticmethod
    async def _handle_failure(context: Context) -> None:
        event_data = SummarizeSecondInstanceCaseJob.get_event_data_from_context_failure(
            context
        )
        normalized_data = await SummarizeSecondInstanceCaseJob._normalize_payload(
            event_data
        )
        payload = _Payload(analysis_id=str(normalized_data['analysis_id']))

        await SummarizeSecondInstanceCaseJob._mark_analysis_as_failed(payload)
