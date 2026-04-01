from typing import Annotated

from fastapi import APIRouter, Depends, Query

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.list_analyses_use_case import ListAnalysesUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.validation.shared import CursorPaginationResponseSchema


class ListAnalysesController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses',
            status_code=200,
            response_model=CursorPaginationResponseSchema[AnalysisDto],
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
        ) -> CursorPaginationResponseSchema[AnalysisDto]:
            use_case = ListAnalysesUseCase(
                analisyses_repository=analisyses_repository,
            )
            response = use_case.execute(
                account_id=account_id.value,
                search=search,
                cursor=cursor,
                limit=limit,
                is_archived=is_archived,
            )

            return CursorPaginationResponseSchema[AnalysisDto](
                items=response.items,
                next_cursor=(
                    response.next_cursor.value
                    if response.next_cursor is not None
                    else None
                ),
            )
