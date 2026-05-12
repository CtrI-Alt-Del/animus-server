from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import AnalysisDocumentsRepository, AnalisysesRepository
from animus.core.intake.use_cases import CreateAnalysisDocumentUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.pubsub_pipe import PubSubPipe


class _Body(BaseModel):
    uploaded_at: str
    file_path: str
    name: str


class CreateAnalysisDocumentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analysis/{analysis_id}/document',
            status_code=201,
            response_model=AnalysisDocumentDto,
        )
        def _(
            analysis_id: str,
            body: _Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            analysis_documents_repository: Annotated[
                AnalysisDocumentsRepository,
                Depends(DatabasePipe.get_analysis_documents_repository_from_request),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> AnalysisDocumentDto:
            IntakePipe.verify_analysis_by_account_from_request(
                analysis_id=analysis_id,
                account_id=account_id,
                analisyses_repository=analisyses_repository,
            )

            use_case = CreateAnalysisDocumentUseCase(
                analysis_documents_repository=analysis_documents_repository,
                analisyses_repository=analisyses_repository,
                broker=broker,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                uploaded_at=body.uploaded_at,
                file_path=body.file_path,
                name=body.name,
            )
