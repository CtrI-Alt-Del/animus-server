from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.petition_summary_mapper import (
    PetitionSummaryMapper,
)
from animus.database.sqlalchemy.models.intake.petition_model import PetitionModel
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

    def find_by_analysis_id(self, analysis_id: Id) -> PetitionSummary | None:
        model = self._sqlalchemy.scalar(
            select(PetitionSummaryModel)
            .join(PetitionModel, PetitionModel.id == PetitionSummaryModel.petition_id)
            .where(PetitionModel.analysis_id == analysis_id.value)
        )
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

        model.case_summary = petition_summary.case_summary.value
        model.legal_issue = petition_summary.legal_issue.value
        model.central_question = petition_summary.central_question.value
        model.relevant_laws = [item.value for item in petition_summary.relevant_laws]
        model.key_facts = [item.value for item in petition_summary.key_facts]
        model.search_terms = [item.value for item in petition_summary.search_terms]
