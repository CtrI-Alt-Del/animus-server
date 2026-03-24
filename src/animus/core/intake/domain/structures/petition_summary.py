from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.structures import Text


@structure
class PetitionSummary(Structure):
    content: Text
    main_points: list[Text]

    @classmethod
    def create(cls, dto: PetitionSummaryDto) -> 'PetitionSummary':
        return cls(
            content=Text.create(dto.content),
            main_points=[Text.create(item) for item in dto.main_points],
        )

    @property
    def dto(self) -> PetitionSummaryDto:
        return PetitionSummaryDto(
            content=self.content.value,
            main_points=[item.value for item in self.main_points],
        )
