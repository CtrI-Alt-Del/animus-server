from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PetitionDraftUnavailableError,
)
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.interfaces import AnalysesRepository, PetitionDraftsRepository
from animus.core.shared.domain.errors.forbidden_error import ForbiddenError
from animus.core.shared.domain.structures import Id


class GetPetitionDraftUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        petition_drafts_repository: PetitionDraftsRepository,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._petition_drafts_repository = petition_drafts_repository

    def execute(self, analysis_id: str, account_id: str) -> PetitionDraftDto:
        analysis_id_entity = Id.create(analysis_id)
        account_id_entity = Id.create(account_id)

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.account_id != account_id_entity:
            raise ForbiddenError('Esta analise nao pertence a sua conta.')

        petition_draft = self._petition_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if petition_draft is None:
            raise PetitionDraftUnavailableError

        return petition_draft.dto
