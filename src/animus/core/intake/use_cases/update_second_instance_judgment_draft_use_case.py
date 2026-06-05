from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceAnalysisRequiredError,
    SecondInstanceJudgmentDraftUnavailableError,
)
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.shared.domain.structures import Id


class UpdateSecondInstanceJudgmentDraftUseCase:
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
        dto: SecondInstanceJudgmentDraftDto,
    ) -> SecondInstanceJudgmentDraftDto:
        analysis_id_entity = Id.create(analysis_id)

        normalized_dto = SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id_entity.value,
            report=dto.report,
            merit_analysis=dto.merit_analysis,
            precedent_adherence_analysis=dto.precedent_adherence_analysis,
            ruling=dto.ruling,
            preliminary_issues=dto.preliminary_issues,
            no_applicable_precedent_notice=dto.no_applicable_precedent_notice,
        )

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_second_instance.is_false:
            raise SecondInstanceAnalysisRequiredError

        existing_judgment_draft = self._judgment_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if existing_judgment_draft is None:
            raise SecondInstanceJudgmentDraftUnavailableError

        judgment_draft = SecondInstanceJudgmentDraft.create(normalized_dto)
        self._judgment_drafts_repository.replace(judgment_draft)

        return judgment_draft.dto
