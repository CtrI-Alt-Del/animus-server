from animus.core.intake.domain.structures.case_assessment_briefing import (
    CaseAssessmentBriefing,
)
from animus.core.intake.domain.structures.dtos.case_assessment_briefing_dto import (
    CaseAssessmentBriefingDto,
)
from animus.database.sqlalchemy.models.intake.case_assessment_briefing_model import (
    CaseAssessmentBriefingModel,
)


class CaseAssessmentBriefingMapper:
    @staticmethod
    def to_entity(model: CaseAssessmentBriefingModel) -> CaseAssessmentBriefing:
        return CaseAssessmentBriefing.create(
            CaseAssessmentBriefingDto(
                analysis_id=model.analysis_id,
                legal_area=model.legal_area,
                court_jurisdiction=model.court_jurisdiction,
                main_claims=model.main_claims,
                intended_thesis=model.intended_thesis,
            )
        )

    @staticmethod
    def to_model(
        briefing: CaseAssessmentBriefing,
    ) -> CaseAssessmentBriefingModel:
        return CaseAssessmentBriefingModel(
            analysis_id=briefing.analysis_id.value,
            legal_area=briefing.legal_area.dto,
            court_jurisdiction=briefing.court_jurisdiction.dto,
            main_claims=briefing.main_claims.value,
            intended_thesis=briefing.intended_thesis.value,
        )
