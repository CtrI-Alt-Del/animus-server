from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake.petition_summary_model import (
    PetitionSummaryModel,
)


class PetitionSummaryMapper:
    @staticmethod
    def to_entity(model: PetitionSummaryModel) -> PetitionSummary:
        return PetitionSummary.create(
            PetitionSummaryDto(
                content=model.content,
                main_points=model.main_points,
            )
        )

    @staticmethod
    def to_model(
        petition_id: Id,
        petition_summary: PetitionSummary,
    ) -> PetitionSummaryModel:
        return PetitionSummaryModel(
            petition_id=petition_id.value,
            content=petition_summary.content.value,
            main_points=[point.value for point in petition_summary.main_points],
        )
