from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.domain.errors import PetitionNotFoundError
from animus.core.intake.interfaces import PetitionsRepository
from animus.core.shared.domain.structures import Id


class GetAnalysisPetitionUseCase:
    def __init__(self, petitions_repository: PetitionsRepository) -> None:
        self._petitions_repository = petitions_repository

    def execute(self, analysis_id: str) -> PetitionDto:
        analysis_id_entity = Id.create(analysis_id)
        petition = self._petitions_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )

        if petition is None:
            raise PetitionNotFoundError

        return petition.dto
