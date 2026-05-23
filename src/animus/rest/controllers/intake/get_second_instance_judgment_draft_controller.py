from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import GetSecondInstanceJudgmentDraftUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class GetSecondInstanceJudgmentDraftController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/petition-drafts',
            status_code=200,
            response_model=SecondInstanceJudgmentDraftDto,
        )
        def _(
            analysis_id: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            judgment_drafts_repository: Annotated[
                SecondInstanceJudgmentDraftsRepository,
                Depends(DatabasePipe.get_judgment_drafts_repository_from_request),
            ],
        ) -> SecondInstanceJudgmentDraftDto:
            use_case = GetSecondInstanceJudgmentDraftUseCase(
                analyses_repository=analyses_repository,
                judgment_drafts_repository=judgment_drafts_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id.value,
            )
