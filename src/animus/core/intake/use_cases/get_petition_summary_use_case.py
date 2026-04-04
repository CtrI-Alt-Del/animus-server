from animus.core.intake.domain.errors import PetitionSummaryUnavailableError
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.interfaces import PetitionSummariesRepository
from animus.core.shared.domain.structures import Id


class GetPetitionSummaryUseCase:
    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository

    def execute(self, petition_id: str) -> PetitionSummaryDto:
        petition_id_entity = Id.create(petition_id)
        petition_summary = self._petition_summaries_repository.find_by_petition_id(
            petition_id=petition_id_entity,
        )

        if petition_summary is None:
            raise PetitionSummaryUnavailableError

        return petition_summary.dto
