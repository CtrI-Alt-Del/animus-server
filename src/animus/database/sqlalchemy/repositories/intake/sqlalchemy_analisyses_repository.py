from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.shared.domain.structures import Id, Integer, Text
from animus.core.shared.responses import CursorPaginationResponse
from animus.database.sqlalchemy.mappers.intake import AnalysisMapper
from animus.database.sqlalchemy.models.intake import AnalysisModel


class SqlalchemyAnalisysesRepository(AnalisysesRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_id(self, analysis_id: Id) -> Analysis | None:
        model = self._sqlalchemy.get(AnalysisModel, analysis_id.value)
        if model is None:
            return None

        return AnalysisMapper.to_entity(model)

    def find_many(
        self,
        search: Text,
        cursor: Id | None,
        limit: Integer,
    ) -> CursorPaginationResponse[Analysis]:
        statement = select(AnalysisModel).where(
            AnalysisModel.name.ilike(f'%{search.value}%')
        )

        if cursor is not None:
            statement = statement.where(AnalysisModel.id > cursor.value)

        models = self._sqlalchemy.scalars(
            statement.order_by(AnalysisModel.id.asc()).limit(limit.value + 1)
        ).all()

        has_next_page = len(models) > limit.value
        slice_models = models[: limit.value]
        items = [AnalysisMapper.to_entity(model) for model in slice_models]

        if not has_next_page:
            return CursorPaginationResponse(items=items, next_cursor=None)

        next_cursor = Id.create(models[limit.value].id)
        return CursorPaginationResponse(items=items, next_cursor=next_cursor)

    def add(self, analysis: Analysis) -> None:
        self._sqlalchemy.add(AnalysisMapper.to_model(analysis))

    def add_many(self, analyses: list[Analysis]) -> None:
        self._sqlalchemy.add_all(
            [AnalysisMapper.to_model(analysis) for analysis in analyses]
        )

    def replace(self, analysis: Analysis) -> None:
        model = self._sqlalchemy.get(AnalysisModel, analysis.id.value)
        if model is None:
            self.add(analysis)
            return

        model.name = analysis.name.value
        model.folder_id = (
            analysis.folder_id.value if analysis.folder_id is not None else None
        )
        model.account_id = analysis.account_id.value
        model.status = analysis.status.value.value
        model.is_archived = analysis.is_archived.value
