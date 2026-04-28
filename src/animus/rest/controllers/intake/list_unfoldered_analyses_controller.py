from typing import Annotated

from fastapi import APIRouter, Depends, Query

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases import ListUnfolderedAnalysesUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import CursorPaginationResponse
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class ListUnfolderedAnalysesController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/unfoldered',
            status_code=200,
            response_model=CursorPaginationResponse[AnalysisDto],
        )
        def _(
            limit: Annotated[int, Query(ge=1)],
            search: str = '',
            cursor: str | None = None,
            is_archived: bool = False,
            account_id: Id = Depends(AuthPipe.get_account_id_from_request),
            analisyses_repository: AnalisysesRepository = Depends(
                DatabasePipe.get_analisyses_repository_from_request
            ),
        ) -> CursorPaginationResponse[AnalysisDto]:
            use_case = ListUnfolderedAnalysesUseCase(
                analisyses_repository=analisyses_repository,
            )
            return use_case.execute(
                account_id=account_id.value,
                search=search,
                cursor=cursor,
                limit=limit,
                is_archived=is_archived,
            )