from typing import Annotated

from fastapi import APIRouter, Depends, Query

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.intake.use_cases.list_analyses_use_case import ListAnalysesUseCase
from animus.core.shared.responses import CursorPaginationResponse
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class ListAnalysesController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses',
            status_code=200,
            response_model=CursorPaginationResponse[AnalysisDto],
        )
        def _(
            limit: Annotated[int, Query(ge=1)],
            search: str = '',
            cursor: str | None = None,
            is_archived: bool = False,
            account_id: Id = Depends(AuthPipe.get_account_id_from_request),
            analyses_repository: AnalysesRepository = Depends(
                DatabasePipe.get_analyses_repository_from_request
            ),
        ) -> CursorPaginationResponse[AnalysisDto]:
            use_case = ListAnalysesUseCase(
                analyses_repository=analyses_repository,
            )
            return use_case.execute(
                account_id=account_id.value,
                search=search,
                cursor=cursor,
                limit=limit,
                is_archived=is_archived,
            )
