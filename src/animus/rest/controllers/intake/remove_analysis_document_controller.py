from typing import Annotated

from fastapi import APIRouter, Depends, Response

from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
)
from animus.core.intake.use_cases import RemoveAnalysisDocumentUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.pubsub_pipe import PubSubPipe


class RemoveAnalysisDocumentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.delete('/analyses/{analysis_id}/documents', status_code=204)
        def _(
            analysis_id: str,
            file_path: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            analysis_documents_repository: Annotated[
                AnalysisDocumentsRepository,
                Depends(DatabasePipe.get_analysis_documents_repository_from_request),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> Response:
            IntakePipe.verify_analysis_by_account_from_request(
                analysis_id=analysis_id,
                account_id=account_id,
                analyses_repository=analyses_repository,
            )

            use_case = RemoveAnalysisDocumentUseCase(
                analysis_documents_repository=analysis_documents_repository,
                analyses_repository=analyses_repository,
                broker=broker,
            )
            use_case.execute(analysis_id=analysis_id, file_path=file_path)
            return Response(status_code=204)
