import asyncio
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from inngest import Context, Inngest, TriggerEvent

from animus.ai.agno.workflows.intake.agno_classify_analysis_precedents_applicability_workflow import (
    AgnoClassifyAnalysisPrecedentsApplicabilityWorkflow,
)
from animus.ai.agno.workflows.intake.agno_summarize_petition_workflow import (
    AgnoSummarizePetitionWorkflow,
)
from animus.constants import Env
from animus.core.auth.domain.errors import AccountNotFoundError
from animus.core.auth.domain.structures import Email
from animus.core.intake.domain.entities.dtos import PetitionDocumentDto
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDatasetDto,
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.use_cases import (
    CreateAnalysisPrecedentApplicabilityFeedbackUseCase,
    CreateAnalysisPrecedentDatasetRowUseCase,
    CreateAnalysisPrecedentsUseCase,
    CreateAnalysisUseCase,
    CreatePetitionUseCase,
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
    SqlalchemyAnalysisPrecedentApplicabilityFeedbacksRepository,
    SqlalchemyAnalysisPrecedentDatasetRowsRepository,
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyAnalisysesRepository,
    SqlalchemyPetitionSummariesRepository,
    SqlalchemyPetitionsRepository,
    SqlalchemyPrecedentsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.intake.petition_summary_embeddings.openai.openai_petition_summary_embeddings_provider import (
    OpenAIPetitionSummaryEmbeddingsProvider,
)
from animus.providers.storage import (
    GcsFileStorageProvider,
    PyarrowParquetProvider,
    PypdfPdfProvider,
    PythonDocxProvider,
)


class _NoopBroker:
    def publish(self, event: Event[Any]) -> None:
        del event


class SeedAnalysesPrecedentsDatasetJob:
    _ACCOUNT_EMAIL = 'animus.ctrlaltdel@gmail.com'
    _PETITIONS_PREFIX = 'intake/xertica/petitions/'
    _DATASET_BUCKET_PREFIX = 'intake/datasets/analysis-precedents/'
    _LOCAL_DATASET_PREFIX = 'tmp/intake/datasets/analysis-precedents/'

    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='seed-analyses-precedents-dataset',
            trigger=TriggerEvent(
                event='intake/seed-analyses-precedents-dataset.requested',
            ),
        )
        async def _(context: Context) -> None:
            account_id = await context.step.run(
                'resolve_account',
                SeedAnalysesPrecedentsDatasetJob._resolve_account,
            )
            petition_file_paths = await context.step.run(
                'list_petition_files',
                SeedAnalysesPrecedentsDatasetJob._list_petition_files,
            )

            all_dataset_rows_data: list[dict[str, Any]] = []
            for index, petition_file_path in enumerate(petition_file_paths, start=1):
                dataset_rows_data = await context.step.run(
                    f'process_file_{index}',
                    lambda account_id=account_id, petition_file_path=petition_file_path: (
                        SeedAnalysesPrecedentsDatasetJob._process_file(
                            account_id=account_id,
                            petition_file_path=petition_file_path,
                        )
                    ),
                )
                all_dataset_rows_data.extend(dataset_rows_data)

            await context.step.run(
                'export_dataset',
                lambda all_dataset_rows_data=all_dataset_rows_data: (
                    SeedAnalysesPrecedentsDatasetJob._export_dataset(
                        all_dataset_rows_data,
                    )
                ),
            )

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
    async def _list_petition_files() -> list[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            SeedAnalysesPrecedentsDatasetJob._list_petition_files_sync,
        )

    @staticmethod
    def _list_petition_files_sync() -> list[str]:
        file_storage_provider = GcsFileStorageProvider()
        bucket = file_storage_provider.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
        blobs = cast(
            'Any',
            bucket.list_blobs(  # pyright: ignore[reportUnknownMemberType]
                prefix=SeedAnalysesPrecedentsDatasetJob._PETITIONS_PREFIX,
            ),
        )

        petition_file_paths: list[str] = []
        for blob in blobs:
            blob_name = getattr(blob, 'name', None)
            if not isinstance(blob_name, str):
                continue

            if blob_name.endswith('/'):
                continue

            if not blob_name.lower().endswith('.pdf'):
                continue

            petition_file_paths.append(blob_name)

        petition_file_paths.sort()
        return petition_file_paths

    @staticmethod
    async def _process_file(
        account_id: str,
        petition_file_path: str,
    ) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: SeedAnalysesPrecedentsDatasetJob._process_file_sync(
                account_id=account_id,
                petition_file_path=petition_file_path,
            ),
        )

    @staticmethod
    def _process_file_sync(
        account_id: str,
        petition_file_path: str,
    ) -> list[dict[str, Any]]:
        with Sqlalchemy.session() as session:
            analisyses_repository = SqlalchemyAnalisysesRepository(session)
            petitions_repository = SqlalchemyPetitionsRepository(session)
            petition_summaries_repository = SqlalchemyPetitionSummariesRepository(
                session
            )
            analysis_precedents_repository = SqlalchemyAnalysisPrecedentsRepository(
                session
            )
            precedents_repository = SqlalchemyPrecedentsRepository(session)
            feedbacks_repository = (
                SqlalchemyAnalysisPrecedentApplicabilityFeedbacksRepository(session)
            )
            dataset_rows_repository = SqlalchemyAnalysisPrecedentDatasetRowsRepository(
                session
            )

            existing_petition = petitions_repository.find_by_document_file_path(
                FilePath.create(petition_file_path)
            )
            if existing_petition is None:
                analysis = CreateAnalysisUseCase(analisyses_repository).execute(
                    account_id=account_id,
                )
                session.flush()
                analysis_id = Id.create(analysis.id).value

                petition = CreatePetitionUseCase(
                    petitions_repository=petitions_repository,
                    analisyses_repository=analisyses_repository,
                    broker=_NoopBroker(),
                ).execute(
                    analysis_id=analysis_id,
                    uploaded_at=Datetime.create_at_now().value.isoformat(),
                    document=PetitionDocumentDto(
                        file_path=petition_file_path,
                        name=Path(petition_file_path).name,
                    ),
                )
                session.flush()
                petition_id = Id.create(petition.id).value

                document_content = GetDocumentContentUseCase(
                    file_storage_provider=GcsFileStorageProvider(),
                    pdf_provider=PypdfPdfProvider(),
                    docx_provider=PythonDocxProvider(),
                ).execute(file_path=FilePath.create(petition_file_path))

                AgnoSummarizePetitionWorkflow(
                    petition_summaries_repository=petition_summaries_repository,
                    petitions_repository=petitions_repository,
                    analisyses_repository=analisyses_repository,
                ).run(
                    petition_id=petition_id,
                    petition_document_content=document_content,
                )
                session.flush()
            else:
                analysis_id = existing_petition.analysis_id.value
                petition_summary = petition_summaries_repository.find_by_analysis_id(
                    analysis_id=existing_petition.analysis_id,
                )
                if petition_summary is None:
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
                    petition_summaries_repository=petition_summaries_repository,
                    petition_summary_embeddings_provider=(
                        OpenAIPetitionSummaryEmbeddingsProvider()
                    ),
                    precedents_embeddings_repository=(
                        QdrantPrecedentsEmbeddingsRepository()
                    ),
                    precedents_repository=precedents_repository,
                ).execute(
                    analysis_id=analysis_id,
                    dto=filters_dto,
                )

                CreateAnalysisPrecedentsUseCase(
                    analysis_precedents_repository=analysis_precedents_repository,
                    analisyses_repository=analisyses_repository,
                ).execute(
                    analysis_id=analysis_id,
                    filters_dto=filters_dto,
                    analysis_precedents=analysis_precedents,
                    synthesis_output=None,
                )
                session.flush()

            dataset_rows = AgnoClassifyAnalysisPrecedentsApplicabilityWorkflow(
                petition_summaries_repository=petition_summaries_repository,
                create_analysis_precedent_applicability_feedback_use_case=(
                    CreateAnalysisPrecedentApplicabilityFeedbackUseCase(
                        feedbacks_repository=feedbacks_repository,
                    )
                ),
                create_analysis_precedent_dataset_row_use_case=(
                    CreateAnalysisPrecedentDatasetRowUseCase(
                        dataset_rows_repository=dataset_rows_repository,
                    )
                ),
            ).run(
                analysis_id=analysis_id,
                analysis_precedents=analysis_precedents,
            )

            return [asdict(dataset_row) for dataset_row in dataset_rows]

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
            f'{SeedAnalysesPrecedentsDatasetJob._DATASET_BUCKET_PREFIX}'
            f'{dataset_identifier}.parquet'
        )

        rows = [
            AnalysisPrecedentDatasetDto(**dataset_row_data)
            for dataset_row_data in all_dataset_rows_data
        ]

        parquet_provider = PyarrowParquetProvider()
        Path(local_file_path.value).parent.mkdir(parents=True, exist_ok=True)
        parquet_provider.write_analysis_precedents_dataset(
            rows=rows,
            local_file_path=local_file_path,
        )

        file_storage_provider = GcsFileStorageProvider()
        bucket = file_storage_provider.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
        blob = bucket.blob(bucket_file_path.value)  # pyright: ignore[reportUnknownMemberType]
        print(local_file_path.value)

        try:
            blob.upload_from_filename(local_file_path.value)  # pyright: ignore[reportUnknownMemberType]
        finally:
            Path(local_file_path.value).unlink(missing_ok=True)
