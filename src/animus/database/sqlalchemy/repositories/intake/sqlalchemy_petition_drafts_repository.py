from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.intake.interfaces.petition_drafts_repository import (
    PetitionDraftsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.petition_draft_mapper import (
    PetitionDraftMapper,
)
from animus.database.sqlalchemy.models.intake.petition_draft_model import (
    PetitionDraftModel,
)


class SqlalchemyPetitionDraftsRepository(PetitionDraftsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(self, analysis_id: Id) -> PetitionDraft | None:
        model = self._sqlalchemy.get(PetitionDraftModel, analysis_id.value)
        if model is None:
            return None

        return PetitionDraftMapper.to_entity(model)

    def add(self, petition_draft: PetitionDraft) -> None:
        self._sqlalchemy.add(PetitionDraftMapper.to_model(petition_draft))

    def replace(self, petition_draft: PetitionDraft) -> None:
        model = self._sqlalchemy.get(
            PetitionDraftModel, petition_draft.analysis_id.value
        )
        if model is None:
            self.add(petition_draft)
            return

        model.structured_facts = petition_draft.structured_facts.value
        model.legal_grounds = petition_draft.legal_grounds.value
        model.central_thesis = petition_draft.central_thesis.value
        model.requests = [item.value for item in petition_draft.requests]
        model.precedent_citations = [
            item.value for item in petition_draft.precedent_citations
        ]
