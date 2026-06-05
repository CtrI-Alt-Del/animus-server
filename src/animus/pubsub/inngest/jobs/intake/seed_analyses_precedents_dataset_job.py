import asyncio
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from inngest import Context, Inngest, TriggerEvent

from animus.ai.agno.workflows.intake.agno_synthesize_analysis_precedents_workflow import (
    AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow,
)
from animus.ai.agno.workflows.intake.agno_summarize_first_instance_case_workflow import (
    AgnoSummarizeFirstInstanceCaseWorkflow,
)
from animus.constants import Env
from animus.core.auth.domain.errors import AccountNotFoundError
from animus.core.auth.domain.structures import Email
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDatasetRowDto,
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.use_cases import (
    CreateAnalysisDocumentUseCase,
    CreateAnalysisUseCase,
    SearchAnalysisPrecedentsUseCase,
)
from animus.core.shared.domain.abstracts import Event
from animus.core.shared.domain.structures import Datetime, FilePath, Id
from animus.core.storage.use_cases import GetDocumentContentUseCase
from animus.database.qdrant.qdrant_precedents_embeddings_repository import (
    QdrantPrecedentsEmbeddingsRepository,
)
from animus.database.sqlalchemy.repositories.auth import SqlalchemyAccountsRepository
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysisDocumentsRepository,
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyAnalysesRepository,
    SqlalchemyCaseSummariesRepository,
    SqlalchemyPrecedentsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.intake.case_summary_embeddings.openai.openai_case_summary_embeddings_provider import (
    OpenAICaseSummaryEmbeddingsProvider,
)
from animus.providers.storage import (
    GcsFileStorageProvider,
    PyarrowParquetProvider,
    PypdfPdfProvider,
    PythonDocxProvider,
)

if TYPE_CHECKING:
    from animus.core.intake.interfaces.petition_summaries_repository import (
        PetitionSummariesRepository,
    )


class _NoopBroker:
    def publish(self, event: Event[Any]) -> None:
        del event


class SeedAnalysesPrecedentsDatasetJob:
    _ACCOUNT_EMAIL = 'animus.ctrlaltdel@gmail.com'
    _DOCUMENTS_PREFIX = 'intake/xertica/documents/'
    _DATASET_PATH_PREFIX = 'intake/datasets/analyses-precedents/'
    _LOCAL_DATASET_PREFIX = 'tmp/intake/datasets/analyses-precedents/'

    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='seed-analyses-precedents-dataset',
            trigger=TriggerEvent(
                event='intake/seed-analyses-precedents-dataset.triggered',
            ),
        )
        async def _(context: Context) -> None:
            account_id = await context.step.run(
                'resolve_account',
                SeedAnalysesPrecedentsDatasetJob._resolve_account,
            )
            document_file_paths = await context.step.run(
                'list_document_files',
                SeedAnalysesPrecedentsDatasetJob._list_document_files,
            )

            all_dataset_rows_data: list[dict[str, Any]] = []
            for index, document_file_path in enumerate(document_file_paths, start=1):
                dataset_rows_data = await context.step.run(
                    f'process_file_{index}',
                    lambda account_id=account_id, document_file_path=document_file_path: (
                        SeedAnalysesPrecedentsDatasetJob._process_file(
                            account_id=account_id,
                            document_file_path=document_file_path,
                        )
                    ),
                )
                all_dataset_rows_data.extend(dataset_rows_data)

        return _

    @staticmethod
    async def _resolve_account() -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            SeedAnalysesPrecedentsDatasetJob._resolve_account_sync,
        )

    @staticmethod
    def _resolve_account_sync() -> str:
        with Sqlalchemy.session() as session:
            account = SqlalchemyAccountsRepository(session).find_by_email(
                Email.create(SeedAnalysesPrecedentsDatasetJob._ACCOUNT_EMAIL),
            )
            if account is None:
                raise AccountNotFoundError

            return account.id.value

    @staticmethod
    async def _list_document_files() -> list[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            SeedAnalysesPrecedentsDatasetJob._list_document_files_sync,
        )

    @staticmethod
    def _list_document_files_sync() -> list[str]:
        file_storage_provider = GcsFileStorageProvider()
        bucket = file_storage_provider.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
        blobs = cast(
            'Any',
            bucket.list_blobs(  # pyright: ignore[reportUnknownMemberType]
                prefix=SeedAnalysesPrecedentsDatasetJob._DOCUMENTS_PREFIX,
            ),
        )

        document_file_paths: list[str] = []
        for blob in blobs:
            blob_name = getattr(blob, 'name', None)
            if not isinstance(blob_name, str):
                continue

            if blob_name.endswith('/'):
                continue

            if not blob_name.lower().endswith('.pdf'):
                continue

            document_file_paths.append(blob_name)

        document_file_paths.sort()
        return document_file_paths

    @staticmethod
    async def _process_file(
        account_id: str,
        document_file_path: str,
    ) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: SeedAnalysesPrecedentsDatasetJob._process_file_sync(
                account_id=account_id,
                document_file_path=document_file_path,
            ),
        )

    @staticmethod
    def _process_file_sync(
        account_id: str,
        document_file_path: str,
    ) -> list[dict[str, Any]]:
        with Sqlalchemy.session() as session:
            analyses_repository = SqlalchemyAnalysesRepository(session)
            analysis_documents_repository = SqlalchemyAnalysisDocumentsRepository(
                session
            )
            case_summaries_repository = SqlalchemyCaseSummariesRepository(session)
            analysis_precedents_repository = SqlalchemyAnalysisPrecedentsRepository(
                session
            )
            precedents_repository = SqlalchemyPrecedentsRepository(session)

            existing_document = analysis_documents_repository.find_by_file_path(
                FilePath.create(document_file_path)
            )
            if existing_document is None:
                analysis = CreateAnalysisUseCase(analyses_repository).execute(
                    account_id=account_id,
                    type=AnalysisType.create_as_first_instance().dto,
                )
                session.flush()
                analysis_id = Id.create(analysis.id).value

                CreateAnalysisDocumentUseCase(
                    analysis_documents_repository=analysis_documents_repository,
                    analyses_repository=analyses_repository,
                    broker=_NoopBroker(),
                ).execute(
                    analysis_id=analysis_id,
                    uploaded_at=Datetime.create_at_now().value.isoformat(),
                    file_path=document_file_path,
                    name=Path(document_file_path).name,
                )
                session.flush()

                document_content = GetDocumentContentUseCase(
                    file_storage_provider=GcsFileStorageProvider(),
                    pdf_provider=PypdfPdfProvider(),
                    docx_provider=PythonDocxProvider(),
                ).execute(file_path=FilePath.create(document_file_path))

                AgnoSummarizeFirstInstanceCaseWorkflow(
                    case_summaries_repository=case_summaries_repository,
                    analyses_repository=analyses_repository,
                ).run(
                    analysis_id=analysis_id,
                    document_content=document_content,
                )
                session.flush()
            else:
                analysis_id = existing_document.analysis_id.value

            case_summary = case_summaries_repository.find_by_analysis_id(
                analysis_id=Id.create(analysis_id),
            )
            if case_summary is None:
                return []

            existing_analysis_precedents = (
                analysis_precedents_repository.find_many_by_analysis_id(
                    analysis_id=Id.create(analysis_id),
                ).items
            )
            if existing_analysis_precedents:
                analysis_precedents = [
                    analysis_precedent.dto
                    for analysis_precedent in existing_analysis_precedents
                ]
            else:
                filters_dto = AnalysisPrecedentsSearchFiltersDto(limit=10)
                analysis_precedents = SearchAnalysisPrecedentsUseCase(
                    case_summaries_repository=case_summaries_repository,
                    case_summary_embeddings_provider=(
                        OpenAICaseSummaryEmbeddingsProvider()
                    ),
                    precedents_embeddings_repository=(
                        QdrantPrecedentsEmbeddingsRepository()
                    ),
                    precedents_repository=precedents_repository,
                ).execute(
                    analysis_id=analysis_id,
                    dto=filters_dto,
                )

                AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow(
                    petition_summaries_repository=cast(
                        'PetitionSummariesRepository',
                        case_summaries_repository,
                    ),
                    analysis_precedents_repository=analysis_precedents_repository,
                    analyses_repository=analyses_repository,
                ).run(
                    analysis_id=analysis_id,
                    filters_dto=filters_dto,
                    analysis_precedents=analysis_precedents,
                )
                session.flush()

                analysis_precedents = [
                    analysis_precedent.dto
                    for analysis_precedent in analysis_precedents_repository.find_many_by_analysis_id(
                        analysis_id=Id.create(analysis_id),
                    ).items
                ]

            return [
                asdict(analysis_precedent) for analysis_precedent in analysis_precedents
            ]

    @staticmethod
    async def _export_dataset(all_dataset_rows_data: list[dict[str, Any]]) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: SeedAnalysesPrecedentsDatasetJob._export_dataset_sync(
                all_dataset_rows_data
            ),
        )

    @staticmethod
    def _export_dataset_sync(all_dataset_rows_data: list[dict[str, Any]]) -> None:
        if not all_dataset_rows_data:
            return

        dataset_identifier = (
            f'{Id.create().value}-{datetime.now(UTC).strftime("%Y%m%d")}'
        )
        local_file_path = FilePath.create(
            f'{SeedAnalysesPrecedentsDatasetJob._LOCAL_DATASET_PREFIX}'
            f'{dataset_identifier}.parquet'
        )
        bucket_file_path = FilePath.create(
            f'{SeedAnalysesPrecedentsDatasetJob._DATASET_PATH_PREFIX}'
            f'{dataset_identifier}.parquet'
        )

        rows = [
            AnalysisPrecedentDatasetRowDto(**dataset_row_data)
            for dataset_row_data in all_dataset_rows_data
        ]

        parquet_provider = PyarrowParquetProvider()
        Path(local_file_path.value).parent.mkdir(parents=True, exist_ok=True)
        parquet_provider.write_analysis_precedents_dataset(
            rows=rows,
            local_file_path=local_file_path,
        )

        file_storage_provider = GcsFileStorageProvider()
        upload_source_path = Path(bucket_file_path.value)
        upload_source_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_file_path.value, upload_source_path)

        try:
            file_storage_provider.upload_files([bucket_file_path])
        finally:
            Path(local_file_path.value).unlink(missing_ok=True)
            upload_source_path.unlink(missing_ok=True)
