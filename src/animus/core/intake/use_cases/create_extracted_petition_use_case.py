from animus.core.intake.domain.structures.dtos.extracted_petition_dto import (
    ExtractedPetitionDto,
)
from animus.core.intake.domain.structures.extracted_petition import ExtractedPetition
from animus.core.intake.interfaces.extracted_petitions_repository import (
    ExtractedPetitionsRepository,
)
from animus.core.shared.domain.structures import Id


class CreateExtractedPetitionUseCase:
    def __init__(
        self,
        extracted_petitions_repository: ExtractedPetitionsRepository,
    ) -> None:
        self._extracted_petitions_repository = extracted_petitions_repository

    def execute(
        self,
        analysis_id: str,
        first_page: int,
        last_page: int,
    ) -> ExtractedPetitionDto:
        extracted_petition = ExtractedPetition.create(
            ExtractedPetitionDto(
                analysis_id=analysis_id,
                first_page=first_page,
                last_page=last_page,
            )
        )

        existing_extracted_petition = (
            self._extracted_petitions_repository.find_by_analysis_id(
                analysis_id=Id.create(analysis_id),
            )
        )

        if existing_extracted_petition is None:
            self._extracted_petitions_repository.add(extracted_petition)
        else:
            self._extracted_petitions_repository.replace(extracted_petition)

        return extracted_petition.dto
