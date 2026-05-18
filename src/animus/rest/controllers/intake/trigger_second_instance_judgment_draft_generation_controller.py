from typing import Annotated

from fastapi import APIRouter, Depends, Response

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import (
    TriggerSecondInstanceJudgmentDraftGenerationUseCase,
)
from animus.core.shared.interfaces import Broker
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.pubsub_pipe import PubSubPipe


class TriggerSecondInstanceJudgmentDraftGenerationController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/second-instance-judgment-drafts', status_code=202
        )
        async def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            case_summaries_repository: Annotated[
                CaseSummariesRepository,
                Depends(DatabasePipe.get_case_summaries_repository_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> Response:
            use_case = TriggerSecondInstanceJudgmentDraftGenerationUseCase(
                analisyses_repository=analisyses_repository,
                case_summaries_repository=case_summaries_repository,
                analysis_precedents_repository=analysis_precedents_repository,
                broker=broker,
            )

            use_case.execute(analysis_id=analysis.id.value)

            return Response(status_code=202)
