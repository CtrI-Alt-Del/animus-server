from typing import Annotated

from fastapi import APIRouter, Depends, Response

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalisysesRepository,
)
from animus.core.intake.use_cases import RequestCaseSummaryUseCase
from animus.core.shared.interfaces import Broker
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.pubsub_pipe import PubSubPipe


class RequestCaseSummaryController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/analysis/{analysis_id}/case-summaries', status_code=202)
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analysis_documents_repository: Annotated[
                AnalysisDocumentsRepository,
                Depends(DatabasePipe.get_analysis_documents_repository_from_request),
            ],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> Response:
            use_case = RequestCaseSummaryUseCase(
                analysis_documents_repository=analysis_documents_repository,
                analisyses_repository=analisyses_repository,
                broker=broker,
            )

            use_case.execute(analysis_id=analysis.id.value)

            return Response(status_code=202)
