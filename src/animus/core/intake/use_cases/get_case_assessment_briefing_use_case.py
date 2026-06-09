from animus.core.intake.domain.errors import CaseAssessmentBriefingNotFoundError
from animus.core.intake.domain.structures.dtos import CaseAssessmentBriefingDto
from animus.core.intake.interfaces import CaseAssessmentBriefingsRepository
from animus.core.shared.domain.structures import Id


class GetCaseAssessmentBriefingUseCase:
    def __init__(
        self,
        case_assessment_briefings_repository: CaseAssessmentBriefingsRepository,
    ) -> None:
        self._case_assessment_briefings_repository = (
            case_assessment_briefings_repository
        )

    def execute(self, analysis_id: str) -> CaseAssessmentBriefingDto:
        analysis_id_entity = Id.create(analysis_id)
        briefing = self._case_assessment_briefings_repository.find_by_analysis_id(
            analysis_id_entity,
        )

        if briefing is None:
            raise CaseAssessmentBriefingNotFoundError

        return briefing.dto
