from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.structures import CaseAssessmentBriefing
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos import CaseAssessmentBriefingDto
from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseAssessmentBriefingsRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import CreateCaseAssessmentBriefingUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id


class TestCreateCaseAssessmentBriefingUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.case_assessment_briefings_repository_mock = create_autospec(
            CaseAssessmentBriefingsRepository,
            instance=True,
        )
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.use_case = CreateCaseAssessmentBriefingUseCase(
            case_assessment_briefings_repository=self.case_assessment_briefings_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            analyses_repository=self.analyses_repository_mock,
        )

    def test_should_add_briefing_and_update_analysis_status_when_briefing_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = None
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None

        result = self.use_case.execute(
            analysis_id=analysis_id,
            legal_area='CIVIL',
            court_jurisdiction='TJSP',
            main_claims='Pedido principal',
            intended_thesis='Tese principal',
        )

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity
        )
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity
        )
        self.case_assessment_briefings_repository_mock.add.assert_called_once()
        self.case_assessment_briefings_repository_mock.replace.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity
        )
        self.case_summaries_repository_mock.remove_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_called_once()

        added_briefing = (
            self.case_assessment_briefings_repository_mock.add.call_args.args[0]
        )
        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]

        assert result == added_briefing.dto
        assert added_briefing.dto == CaseAssessmentBriefingDto(
            analysis_id=analysis_id,
            legal_area='CIVIL',
            court_jurisdiction='TJSP',
            main_claims='Pedido principal',
            intended_thesis='Tese principal',
        )
        assert (
            updated_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_briefing_submitted()
        )

    def test_should_replace_briefing_remove_case_summary_and_update_analysis_status_when_briefing_already_exists(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_case_analyzed().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = self._create_briefing(
            analysis_id=analysis_id,
            legal_area='TRIBUTARIO',
            court_jurisdiction='TJRJ',
            main_claims='Pedido antigo',
            intended_thesis='Tese antiga',
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = object()

        result = self.use_case.execute(
            analysis_id=analysis_id,
            legal_area='CIVIL',
            court_jurisdiction='TJSP',
            main_claims='Pedido principal atualizado',
            intended_thesis='Tese principal atualizada',
        )

        self.case_assessment_briefings_repository_mock.add.assert_not_called()
        self.case_assessment_briefings_repository_mock.replace.assert_called_once()
        self.case_summaries_repository_mock.remove_by_analysis_id.assert_called_once_with(
            analysis_id_entity
        )
        self.analyses_repository_mock.replace.assert_called_once()

        replaced_briefing = (
            self.case_assessment_briefings_repository_mock.replace.call_args.args[0]
        )
        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]

        assert result == replaced_briefing.dto
        assert replaced_briefing.dto == CaseAssessmentBriefingDto(
            analysis_id=analysis_id,
            legal_area='CIVIL',
            court_jurisdiction='TJSP',
            main_claims='Pedido principal atualizado',
            intended_thesis='Tese principal atualizada',
        )
        assert (
            updated_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_briefing_submitted()
        )

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=Id.create().value,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='Pedido principal',
                intended_thesis='Tese principal',
            )

        self.case_assessment_briefings_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_assessment_briefings_repository_mock.add.assert_not_called()
        self.case_assessment_briefings_repository_mock.replace.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_summaries_repository_mock.remove_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_inconsistent_analysis_type_error_when_analysis_is_not_case_assessment(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.analyses_repository_mock.find_by_id.return_value = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_first_instance().dto,
            status=FirstInstanceAnalysisStatus.create_as_document_uploaded().dto,
        )

        with pytest.raises(
            InconsistentAnalysisTypeError,
            match=r'Tipo de análise incoerente|Tipo de analise incoerente',
        ):
            self.use_case.execute(
                analysis_id=analysis_id,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='Pedido principal',
                intended_thesis='Tese principal',
            )

        self.case_assessment_briefings_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_assessment_briefings_repository_mock.add.assert_not_called()
        self.case_assessment_briefings_repository_mock.replace.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_summaries_repository_mock.remove_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_validation_error_when_main_claims_is_blank(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(
            ValidationError,
            match=r'Pedido principal obrigatorio|Pedido principal obrigatório',
        ):
            self.use_case.execute(
                analysis_id=analysis_id,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='   ',
                intended_thesis='Tese principal',
            )

        self.case_assessment_briefings_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_assessment_briefings_repository_mock.add.assert_not_called()
        self.case_assessment_briefings_repository_mock.replace.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_summaries_repository_mock.remove_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

    @staticmethod
    def _create_analysis(
        analysis_id: str,
        analysis_type: str,
        status: str,
    ) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=status,
                created_at='2026-03-31T10:30:00+00:00',
                type=analysis_type,
            )
        )

    @staticmethod
    def _create_briefing(
        analysis_id: str,
        legal_area: str,
        court_jurisdiction: str,
        main_claims: str,
        intended_thesis: str,
    ) -> CaseAssessmentBriefing:
        return CaseAssessmentBriefing.create(
            CaseAssessmentBriefingDto(
                analysis_id=analysis_id,
                legal_area=legal_area,
                court_jurisdiction=court_jurisdiction,
                main_claims=main_claims,
                intended_thesis=intended_thesis,
            )
        )
