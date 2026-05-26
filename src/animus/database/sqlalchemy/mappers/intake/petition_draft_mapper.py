from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.database.sqlalchemy.models.intake.petition_draft_model import (
    PetitionDraftModel,
)


class PetitionDraftMapper:
    @staticmethod
    def to_entity(model: PetitionDraftModel) -> PetitionDraft:
        return PetitionDraft.create(
            PetitionDraftDto(
                analysis_id=model.analysis_id,
                structured_facts=model.structured_facts,
                legal_grounds=model.legal_grounds,
                central_thesis=model.central_thesis,
                requests=model.requests,
                precedent_citations=model.precedent_citations,
            )
        )

    @staticmethod
    def to_model(petition_draft: PetitionDraft) -> PetitionDraftModel:
        return PetitionDraftModel(
            analysis_id=petition_draft.analysis_id.value,
            structured_facts=petition_draft.structured_facts.value,
            legal_grounds=petition_draft.legal_grounds.value,
            central_thesis=petition_draft.central_thesis.value,
            requests=[item.value for item in petition_draft.requests],
            precedent_citations=[
                item.value for item in petition_draft.precedent_citations
            ],
        )
