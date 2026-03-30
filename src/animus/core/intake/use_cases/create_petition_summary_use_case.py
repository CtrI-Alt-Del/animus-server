from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.shared.domain.structures import Id


class CreatePetitionSummaryUseCase:
    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository

    def execute(self, petition_id: str, dto: PetitionSummaryDto) -> PetitionSummaryDto:
        petition_id_entity = Id.create(petition_id)
        petition_summary = PetitionSummary.create(dto)

        existing_summary = self._petition_summaries_repository.find_by_petition_id(
            petition_id=petition_id_entity,
        )

        if existing_summary is None:
            self._petition_summaries_repository.add(
                petition_id=petition_id_entity,
                petition_summary=petition_summary,
            )
        else:
            self._petition_summaries_repository.replace(
                petition_id=petition_id_entity,
                petition_summary=petition_summary,
            )

        return petition_summary.dto
