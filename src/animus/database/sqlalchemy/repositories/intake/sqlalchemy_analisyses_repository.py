from sqlalchemy import Integer as SqlalchemyInteger
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.shared.domain.structures import Id, Integer, Logical, Text
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
        account_id: Id,
        search: Text,
        cursor: Id | None,
        limit: Integer,
        is_archived: Logical,
        statuses: tuple[AnalysisStatusValue, ...],
    ) -> CursorPaginationResponse[Analysis]:
        status_values = [status.value for status in statuses]

        statement = select(AnalysisModel).where(
            AnalysisModel.account_id == account_id.value,
            AnalysisModel.is_archived == is_archived.value,
            AnalysisModel.name.ilike(f'%{search.value}%'),
            AnalysisModel.status.in_(status_values),
        )

        if cursor is not None:
            statement = statement.where(AnalysisModel.id < cursor.value)

        models = self._sqlalchemy.scalars(
            statement.order_by(AnalysisModel.id.desc()).limit(limit.value + 1)
        ).all()

        has_next_page = len(models) > limit.value
        slice_models = models[: limit.value]
        items = [AnalysisMapper.to_entity(model) for model in slice_models]

        if not has_next_page:
            return CursorPaginationResponse(items=items, next_cursor=None)

        next_cursor = Id.create(slice_models[-1].id)
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

        if analysis.precedents_search_filters is None:
            model.precedents_search_courts = None
            model.precedents_search_precedent_kinds = None
            model.precedents_search_limit = None
        else:
            model.precedents_search_courts = [
                court.dto for court in analysis.precedents_search_filters.courts
            ]
            model.precedents_search_precedent_kinds = [
                precedent_kind.dto
                for precedent_kind in analysis.precedents_search_filters.precedent_kinds
            ]
            model.precedents_search_limit = (
                analysis.precedents_search_filters.limit.value
            )
