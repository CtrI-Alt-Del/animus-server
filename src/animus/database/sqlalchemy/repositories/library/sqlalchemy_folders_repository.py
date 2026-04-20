from sqlalchemy import func, select
from sqlalchemy.orm import Session

from animus.core.library.domain.entities import Folder
from animus.core.library.interfaces import FoldersRepository
from animus.core.shared.domain.structures import Id, Integer, Text
from animus.core.shared.responses import CursorPaginationResponse
from animus.database.sqlalchemy.mappers.library import FolderMapper
from animus.database.sqlalchemy.models.intake import AnalysisModel
from animus.database.sqlalchemy.models.library import FolderModel


class SqlalchemyFoldersRepository(FoldersRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_id(self, folder_id: Id) -> Folder | None:
        row = self._sqlalchemy.execute(
            select(FolderModel, self._analysis_count_subquery()).where(
                FolderModel.id == folder_id.value
            )
        ).one_or_none()
        if row is None:
            return None

        model, analysis_count = row
        return FolderMapper.to_entity(model, analysis_count=analysis_count)

    def find_many(
        self,
        account_id: Id,
        search: Text,
        cursor: Id | None,
        limit: Integer,
    ) -> CursorPaginationResponse[Folder]:
        statement = select(FolderModel, self._analysis_count_subquery()).where(
            FolderModel.account_id == account_id.value,
            FolderModel.is_archived.is_(False),
            FolderModel.name.ilike(f'%{search.value}%'),
        )

        if cursor is not None:
            statement = statement.where(FolderModel.id > cursor.value)

        rows = self._sqlalchemy.execute(
            statement.order_by(FolderModel.id.asc()).limit(limit.value + 1)
        ).all()

        has_next_page = len(rows) > limit.value
        slice_rows = rows[: limit.value]
        items = [
            FolderMapper.to_entity(model, analysis_count=analysis_count)
            for model, analysis_count in slice_rows
        ]

        if not has_next_page:
            return CursorPaginationResponse(items=items, next_cursor=None)

        next_cursor = Id.create(slice_rows[-1][0].id)
        return CursorPaginationResponse(items=items, next_cursor=next_cursor)

    def add(self, folder: Folder) -> None:
        self._sqlalchemy.add(FolderMapper.to_model(folder))

    def add_many(self, folders: list[Folder]) -> None:
        self._sqlalchemy.add_all([FolderMapper.to_model(folder) for folder in folders])

    def replace(self, folder: Folder) -> None:
        model = self._sqlalchemy.get(FolderModel, folder.id.value)
        if model is None:
            self.add(folder)
            return

        model.name = folder.name.value
        model.account_id = folder.account_id.value
        model.is_archived = folder.is_archived.value

    @staticmethod
    def _analysis_count_subquery():
        return (
            select(func.count(AnalysisModel.id))
            .where(
                AnalysisModel.folder_id == FolderModel.id,
                AnalysisModel.is_archived.is_(False),
            )
            .scalar_subquery()
            .label('analysis_count')
        )
