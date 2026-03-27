from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.database.sqlalchemy.models.intake.petition_model import PetitionModel


class PetitionMapper:
    @staticmethod
    def to_entity(model: PetitionModel) -> Petition:
        return Petition.create(
            PetitionDto(
                id=model.id,
                analysis_id=model.analysis_id,
                uploaded_at=model.uploaded_at.isoformat(),
                document=PetitionDocumentDto(
                    file_path=model.document_file_path,
                    name=model.document_name,
                ),
            )
        )

    @staticmethod
    def to_model(entity: Petition) -> PetitionModel:
        return PetitionModel(
            id=entity.id.value,
            analysis_id=entity.analysis_id.value,
            uploaded_at=entity.uploaded_at.value,
            document_file_path=entity.document.file_path.value,
            document_name=entity.document.name.value,
        )
