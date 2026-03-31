from animus.core.intake.domain.entities.dtos import PetitionDto
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisPetitionDto:
    petition: PetitionDto
    summary: PetitionSummaryDto | None
