from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.case_assessment_briefing import (
    CaseAssessmentBriefing,
)
from animus.core.intake.interfaces.case_assessment_briefings_repository import (
    CaseAssessmentBriefingsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.case_assessment_briefing_mapper import (
    CaseAssessmentBriefingMapper,
)
from animus.database.sqlalchemy.models.intake.case_assessment_briefing_model import (
    CaseAssessmentBriefingModel,
)


class SqlalchemyCaseAssessmentBriefingsRepository(CaseAssessmentBriefingsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(self, analysis_id: Id) -> CaseAssessmentBriefing | None:
        model = self._sqlalchemy.get(CaseAssessmentBriefingModel, analysis_id.value)
        if model is None:
            return None

        return CaseAssessmentBriefingMapper.to_entity(model)

    def add(self, briefing: CaseAssessmentBriefing) -> None:
        self._sqlalchemy.add(CaseAssessmentBriefingMapper.to_model(briefing))

    def replace(self, briefing: CaseAssessmentBriefing) -> None:
        model = self._sqlalchemy.get(
            CaseAssessmentBriefingModel,
            briefing.analysis_id.value,
        )
        if model is None:
            self.add(briefing)
            return

        model.legal_area = briefing.legal_area.dto
        model.court_jurisdiction = briefing.court_jurisdiction.dto
        model.main_claims = briefing.main_claims.value
        model.intended_thesis = briefing.intended_thesis.value
