from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import CaseAssessmentBriefingNotFoundError
from animus.core.intake.domain.structures import CaseAssessmentBriefing
from animus.core.intake.domain.structures.dtos import CaseAssessmentBriefingDto
from animus.core.intake.interfaces import CaseAssessmentBriefingsRepository
from animus.core.intake.use_cases import GetCaseAssessmentBriefingUseCase
from animus.core.shared.domain.structures import Id


class TestGetCaseAssessmentBriefingUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.case_assessment_briefings_repository_mock = create_autospec(
            CaseAssessmentBriefingsRepository,
            instance=True,
        )
        self.use_case = GetCaseAssessmentBriefingUseCase(
            case_assessment_briefings_repository=(
                self.case_assessment_briefings_repository_mock
            ),
        )

    def test_should_return_briefing_dto_when_briefing_exists(self) -> None:
        analysis_id = Id.create().value
        briefing = CaseAssessmentBriefing.create(
            CaseAssessmentBriefingDto(
                analysis_id=analysis_id,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='Pedido principal',
                intended_thesis='Tese pretendida',
            )
        )
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = (
            briefing
        )

        result = self.use_case.execute(analysis_id=analysis_id)

        assert result == briefing.dto

    def test_should_raise_not_found_error_when_briefing_does_not_exist(self) -> None:
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = (
            None
        )

        with pytest.raises(CaseAssessmentBriefingNotFoundError):
            self.use_case.execute(analysis_id=Id.create().value)
