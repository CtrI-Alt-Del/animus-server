from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.shared.domain.structures import Id, Integer, Logical, Text
from animus.core.shared.responses import CursorPaginationResponse


class ListAnalysesUseCase:
    def __init__(self, analisyses_repository: AnalisysesRepository) -> None:
        self._analisyses_repository = analisyses_repository

    def execute(
        self,
        account_id: str,
        search: str,
        cursor: str | None,
        limit: int,
        is_archived: bool,
    ) -> CursorPaginationResponse[AnalysisDto]:
        normalized_account_id = Id.create(account_id)
        normalized_search = Text.create(search)
        normalized_cursor = Id.create(cursor) if cursor is not None else None
        normalized_limit = Integer.create(limit)
        normalized_is_archived = Logical.create(is_archived)

        analyses = self._analisyses_repository.find_many(
            account_id=normalized_account_id,
            search=normalized_search,
            cursor=normalized_cursor,
            limit=normalized_limit,
            is_archived=normalized_is_archived,
        )

        return CursorPaginationResponse(
            items=[analysis.dto for analysis in analyses.items],
            next_cursor=analyses.next_cursor,
        )
