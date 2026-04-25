import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.ai.agno.workflows.intake.agno_summarize_petition_workflow import (
    AgnoSummarizePetitionWorkflow,
)
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.errors import PetitionNotFoundError
from animus.core.intake.domain.events import PetitionSummaryRequestedEvent
from animus.core.intake.use_cases import UpdateAnalysisStatusUseCase
from animus.core.shared.domain.structures import Id
from animus.core.storage.use_cases import GetDocumentContentUseCase
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalisysesRepository,
    SqlalchemyPetitionSummariesRepository,
    SqlalchemyPetitionsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.storage import (
    GcsFileStorageProvider,
    PypdfPdfProvider,
    PythonDocxProvider,
)


@dataclass(frozen=True)
class _Payload:
    petition_id: str


class SummarizePetitionJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='summarize-petition',
            trigger=TriggerEvent(event=PetitionSummaryRequestedEvent.name),
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                SummarizePetitionJob._normalize_payload,
                data,
            )
            payload = _Payload(petition_id=str(normalized_data['petition_id']))

            try:
                await context.step.run(
                    'summarize_petition',
                    lambda payload=payload: SummarizePetitionJob._summarize_petition(
                        payload
                    ),
                )
            except Exception:
                await context.step.run(
                    'mark_analysis_as_failed',
                    lambda payload=payload: (
                        SummarizePetitionJob._mark_analysis_as_failed(payload)
                    ),
                )
                raise

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {'petition_id': str(data['petition_id'])}

    @staticmethod
    async def _summarize_petition(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: SummarizePetitionJob._summarize_petition_sync(payload),
        )

    @staticmethod
    def _summarize_petition_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            petitions_repository = SqlalchemyPetitionsRepository(session)
            petition_summaries_repository = SqlalchemyPetitionSummariesRepository(
                session
            )
            analisyses_repository = SqlalchemyAnalisysesRepository(session)

            petition = petitions_repository.find_by_id(Id.create(payload.petition_id))
            print('JOB -> petition', petition)
            if petition is None:
                raise PetitionNotFoundError

            document_content = GetDocumentContentUseCase(
                file_storage_provider=GcsFileStorageProvider(),
                pdf_provider=PypdfPdfProvider(),
                docx_provider=PythonDocxProvider(),
            ).execute(file_path=petition.document.file_path)
            print('JOB -> document_content', document_content)

            workflow = AgnoSummarizePetitionWorkflow(
                petition_summaries_repository=petition_summaries_repository,
                petitions_repository=petitions_repository,
                analisyses_repository=analisyses_repository,
            )
            workflow.run(
                petition_id=petition.id.value,
                petition_document_content=document_content,
            )

    @staticmethod
    async def _mark_analysis_as_failed(payload: _Payload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: SummarizePetitionJob._mark_analysis_as_failed_sync(payload),
        )

    @staticmethod
    def _mark_analysis_as_failed_sync(payload: _Payload) -> None:
        with Sqlalchemy.session() as session:
            petitions_repository = SqlalchemyPetitionsRepository(session)
            petition = petitions_repository.find_by_id(Id.create(payload.petition_id))
            if petition is None:
                return

            UpdateAnalysisStatusUseCase(
                SqlalchemyAnalisysesRepository(session)
            ).execute(
                analysis_id=petition.analysis_id.value,
                status=AnalysisStatusValue.FAILED.value,
            )
