from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.interfaces import SecondInstanceJudgmentDraftsRepository
from animus.core.intake.use_cases import GetSecondInstanceJudgmentDraftUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class GetSecondInstanceJudgmentDraftController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/second-instance-judgment-drafts',
            status_code=200,
            response_model=SecondInstanceJudgmentDraftDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            judgment_drafts_repository: Annotated[
                SecondInstanceJudgmentDraftsRepository,
                Depends(DatabasePipe.get_judgment_drafts_repository_from_request),
            ],
        ) -> SecondInstanceJudgmentDraftDto:
            use_case = GetSecondInstanceJudgmentDraftUseCase(
                judgment_drafts_repository=judgment_drafts_repository,
            )

            return use_case.execute(analysis_id=analysis.id.value)
