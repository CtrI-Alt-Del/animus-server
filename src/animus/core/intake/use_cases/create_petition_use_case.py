from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository


class CreatePetitionUseCase:
    def __init__(self, petitions_repository: PetitionsRepository) -> None:
        self._petitions_repository = petitions_repository

    def execute(
        self,
        analysis_id: str,
        uploaded_at: str,
        document: PetitionDocumentDto,
    ) -> PetitionDto:
        petition = Petition.create(
            PetitionDto(
                analysis_id=analysis_id,
                uploaded_at=uploaded_at,
                document=document,
            )
        )

        self._petitions_repository.add(petition)

        return petition.dto
