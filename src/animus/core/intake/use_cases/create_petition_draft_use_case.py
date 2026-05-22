from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.intake.interfaces import AnalysesRepository, PetitionDraftsRepository
from animus.core.shared.domain.structures import Id


class CreatePetitionDraftUseCase:
    def __init__(
        self,
        petition_drafts_repository: PetitionDraftsRepository,
        analyses_repository: AnalysesRepository,
    ) -> None:
        self._petition_drafts_repository = petition_drafts_repository
        self._analyses_repository = analyses_repository

    def execute(self, analysis_id: str, dto: PetitionDraftDto) -> PetitionDraftDto:
        analysis_id_entity = Id.create(analysis_id)

        normalized_dto = PetitionDraftDto(
            analysis_id=analysis_id_entity.value,
            structured_facts=dto.structured_facts,
            legal_grounds=dto.legal_grounds,
            central_thesis=dto.central_thesis,
            requests=dto.requests,
            precedent_citations=dto.precedent_citations,
        )

        petition_draft = PetitionDraft.create(normalized_dto)

        existing_petition_draft = self._petition_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if existing_petition_draft is None:
            self._petition_drafts_repository.add(petition_draft)
        else:
            self._petition_drafts_repository.replace(petition_draft)

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_case_analysis.is_false:
            raise InconsistentAnalysisTypeError

        analysis.set_status(CaseAssessmentAnalysisStatus.create_as_done())
        self._analyses_repository.replace(analysis)

        return petition_draft.dto
