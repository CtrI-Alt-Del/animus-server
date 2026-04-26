from animus.core.library.domain.entities import Folder
from animus.core.library.domain.entities.dtos import FolderDto
from animus.database.sqlalchemy.models.library import FolderModel


class FolderMapper:
    @staticmethod
    def to_entity(model: FolderModel, analysis_count: int = 0) -> Folder:
        return Folder.create(
            FolderDto(
                id=model.id,
                name=model.name,
                analysis_count=analysis_count,
                account_id=model.account_id,
                is_archived=model.is_archived,
            )
        )

    @staticmethod
    def to_model(entity: Folder) -> FolderModel:
        return FolderModel(
            id=entity.id.value,
            name=entity.name.value,
            account_id=entity.account_id.value,
            is_archived=entity.is_archived.value,
        )
