from animus.core.intake.domain.errors import SecondInstanceJudgmentDraftUnavailableError
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.interfaces import SecondInstanceJudgmentDraftsRepository
from animus.core.shared.domain.structures import Id


class GetSecondInstanceJudgmentDraftUseCase:
    def __init__(
        self,
        judgment_drafts_repository: SecondInstanceJudgmentDraftsRepository,
    ) -> None:
        self._judgment_drafts_repository = judgment_drafts_repository

    def execute(self, analysis_id: str) -> SecondInstanceJudgmentDraftDto:
        analysis_id_entity = Id.create(analysis_id)
        judgment_draft = self._judgment_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )

        if judgment_draft is None:
            raise SecondInstanceJudgmentDraftUnavailableError

        return judgment_draft.dto
