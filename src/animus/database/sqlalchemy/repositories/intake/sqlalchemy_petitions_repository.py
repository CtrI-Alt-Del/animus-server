from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.shared.domain.structures import FilePath, Id
from animus.core.shared.responses import ListResponse
from animus.database.sqlalchemy.mappers.intake.petition_mapper import PetitionMapper
from animus.database.sqlalchemy.models.intake.petition_model import PetitionModel


class SqlalchemyPetitionsRepository(PetitionsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_id(self, petition_id: Id) -> Petition | None:
        model = self._sqlalchemy.get(PetitionModel, petition_id.value)
        if model is None:
            return None

        return PetitionMapper.to_entity(model)

    def find_by_analysis_id(self, analysis_id: Id) -> Petition | None:
        model = self._sqlalchemy.scalar(
            select(PetitionModel).where(PetitionModel.analysis_id == analysis_id.value)
        )
        if model is None:
            return None

        return PetitionMapper.to_entity(model)

    def find_by_document_file_path(self, file_path: FilePath) -> Petition | None:
        model = self._sqlalchemy.scalar(
            select(PetitionModel).where(
                PetitionModel.document_file_path == file_path.value
            )
        )
        if model is None:
            return None

        return PetitionMapper.to_entity(model)

    def find_all_by_analysis_id_ordered_by_uploaded_at(
        self,
        analysis_id: Id,
    ) -> ListResponse[Petition]:
        models = self._sqlalchemy.scalars(
            select(PetitionModel)
            .where(PetitionModel.analysis_id == analysis_id.value)
            .order_by(PetitionModel.uploaded_at.asc())
        ).all()

        return ListResponse(items=[PetitionMapper.to_entity(model) for model in models])

    def add(self, petition: Petition) -> None:
        self._sqlalchemy.add(PetitionMapper.to_model(petition))

    def add_many(self, petitions: list[Petition]) -> None:
        self._sqlalchemy.add_all(
            [PetitionMapper.to_model(petition) for petition in petitions]
        )

    def remove(self, petition_id: Id) -> None:
        model = self._sqlalchemy.get(PetitionModel, petition_id.value)
        if model is None:
            return

        self._sqlalchemy.delete(model)
