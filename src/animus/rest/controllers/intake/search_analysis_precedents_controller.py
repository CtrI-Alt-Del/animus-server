from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseSummariesRepository,
    SecondInstanceDecisionsRepository,
)
from animus.core.intake.use_cases import RequestAnalysisPrecedentsSearchUseCase
from animus.core.shared.interfaces import Broker
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.pubsub_pipe import PubSubPipe
from animus.validation.shared import IdSchema


class _Body(BaseModel):
    courts: list[str] = []
    precedent_kinds: list[str] = []
    limit: int = 10

    def to_dto(self) -> AnalysisPrecedentsSearchFiltersDto:
        return AnalysisPrecedentsSearchFiltersDto(
            courts=self.courts,
            precedent_kinds=self.precedent_kinds,
            limit=self.limit,
        )


class SearchAnalysisPrecedentsController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/analyses/{analysis_id}/precedents/search', status_code=202)
        def _(
            analysis_id: IdSchema,
            body: _Body,
            _analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            second_instance_decisions_repository: Annotated[
                SecondInstanceDecisionsRepository,
                Depends(
                    DatabasePipe.get_second_instance_decisions_repository_from_request
                ),
            ],
            case_summaries_repository: Annotated[
                CaseSummariesRepository,
                Depends(DatabasePipe.get_case_summaries_repository_from_request),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> Response:
            use_case = RequestAnalysisPrecedentsSearchUseCase(
                analyses_repository=analyses_repository,
                second_instance_decisions_repository=second_instance_decisions_repository,
                case_summaries_repository=case_summaries_repository,
                broker=broker,
            )
            use_case.execute(analysis_id=analysis_id, dto=body.to_dto())
            return Response(status_code=202)
