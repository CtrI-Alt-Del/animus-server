from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.structures import CaseAssessmentBriefing
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos import CaseAssessmentBriefingDto
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseAssessmentBriefingsRepository,
    CaseSummariesRepository,
)
from animus.core.shared.domain.structures import Id


class CreateCaseAssessmentBriefingUseCase:
    def __init__(
        self,
        case_assessment_briefings_repository: CaseAssessmentBriefingsRepository,
        case_summaries_repository: CaseSummariesRepository,
        analyses_repository: AnalysesRepository,
    ) -> None:
        self._case_assessment_briefings_repository = (
            case_assessment_briefings_repository
        )
        self._case_summaries_repository = case_summaries_repository
        self._analyses_repository = analyses_repository

    def execute(
        self,
        analysis_id: str,
        legal_area: str,
        court_jurisdiction: str,
        main_claims: str,
        intended_thesis: str,
    ) -> CaseAssessmentBriefingDto:
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_case_analysis.is_false:
            raise InconsistentAnalysisTypeError

        briefing = CaseAssessmentBriefing.create(
            CaseAssessmentBriefingDto(
                analysis_id=analysis_id_entity.value,
                legal_area=legal_area,
                court_jurisdiction=court_jurisdiction,
                main_claims=main_claims,
                intended_thesis=intended_thesis,
            )
        )

        existing_briefing = (
            self._case_assessment_briefings_repository.find_by_analysis_id(
                analysis_id_entity
            )
        )
        if existing_briefing is None:
            self._case_assessment_briefings_repository.add(briefing)
        else:
            self._case_assessment_briefings_repository.replace(briefing)

        existing_case_summary = self._case_summaries_repository.find_by_analysis_id(
            analysis_id_entity
        )
        if existing_case_summary is not None:
            self._case_summaries_repository.remove_by_analysis_id(analysis_id_entity)

        analysis.set_status(CaseAssessmentAnalysisStatus.create_as_briefing_submitted())
        self._analyses_repository.replace(analysis)

        return briefing.dto
