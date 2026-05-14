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
                content=model.content,
            )
        )

    @staticmethod
    def to_model(petition_draft: PetitionDraft) -> PetitionDraftModel:
        return PetitionDraftModel(
            analysis_id=petition_draft.analysis_id.value,
            content=petition_draft.content.value,
        )
