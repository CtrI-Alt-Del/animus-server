from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field, field_validator

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import (
    TriggerSecondInstanceJudgmentDraftRegenerationUseCase,
)
from animus.core.shared.interfaces import Broker
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.pubsub_pipe import PubSubPipe


class _Body(BaseModel):
    comments: str = Field(..., min_length=1)

    @field_validator('comments')
    @classmethod
    def validate_comments(cls, value: str) -> str:
        normalized_value = value.strip()
        if normalized_value == '':
            raise ValueError('Comments must not be blank')
        return normalized_value


class TriggerSecondInstanceJudgmentDraftRegenerationController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/judgment-drafts/regenerate', status_code=202
        )
        async def _(
            body: _Body,
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            judgment_drafts_repository: Annotated[
                SecondInstanceJudgmentDraftsRepository,
                Depends(DatabasePipe.get_judgment_drafts_repository_from_request),
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
            use_case = TriggerSecondInstanceJudgmentDraftRegenerationUseCase(
                analyses_repository=analyses_repository,
                judgment_drafts_repository=judgment_drafts_repository,
                case_summaries_repository=case_summaries_repository,
                analysis_precedents_repository=analysis_precedents_repository,
                broker=broker,
            )

            use_case.execute(analysis_id=analysis.id.value, comments=body.comments)

            return Response(status_code=202)
