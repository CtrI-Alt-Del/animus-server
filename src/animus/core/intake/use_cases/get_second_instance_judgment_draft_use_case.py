from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceAnalysisRequiredError,
    SecondInstanceJudgmentDraftUnavailableError,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.shared.domain.errors import ForbiddenError
from animus.core.shared.domain.structures import Id


class GetSecondInstanceJudgmentDraftUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        judgment_drafts_repository: SecondInstanceJudgmentDraftsRepository,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._judgment_drafts_repository = judgment_drafts_repository

    def execute(
        self,
        analysis_id: str,
        account_id: str,
    ) -> SecondInstanceJudgmentDraftDto:
        analysis_id_entity = Id.create(analysis_id)
        account_id_entity = Id.create(account_id)

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.account_id != account_id_entity:
            raise ForbiddenError('Esta analise nao pertence a sua conta.')

        if analysis.type != AnalysisType.create_as_second_instance():
            raise SecondInstanceAnalysisRequiredError

        judgment_draft = self._judgment_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )

        if judgment_draft is None:
            raise SecondInstanceJudgmentDraftUnavailableError

        return judgment_draft.dto
