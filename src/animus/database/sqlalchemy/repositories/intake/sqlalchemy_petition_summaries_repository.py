from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.petition_summary_mapper import (
    PetitionSummaryMapper,
)
from animus.database.sqlalchemy.models.intake.petition_summary_model import (
    PetitionSummaryModel,
)


class SqlalchemyPetitionSummariesRepository(PetitionSummariesRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_petition_id(self, petition_id: Id) -> PetitionSummary | None:
        model = self._sqlalchemy.get(PetitionSummaryModel, petition_id.value)
        if model is None:
            return None

        return PetitionSummaryMapper.to_entity(model)

    def add(self, petition_id: Id, petition_summary: PetitionSummary) -> None:
        self._sqlalchemy.add(
            PetitionSummaryMapper.to_model(
                petition_id=petition_id,
                petition_summary=petition_summary,
            )
        )

    def replace(self, petition_id: Id, petition_summary: PetitionSummary) -> None:
        model = self._sqlalchemy.get(PetitionSummaryModel, petition_id.value)
        if model is None:
            self.add(petition_id=petition_id, petition_summary=petition_summary)
            return

        model.content = petition_summary.content.value
        model.main_points = [point.value for point in petition_summary.main_points]
