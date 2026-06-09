from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceAnalysisRequiredError,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import CreateSecondInstanceJudgmentDraftUseCase
from animus.core.shared.domain.structures import Id


class TestCreateSecondInstanceJudgmentDraftUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.judgment_drafts_repository_mock = create_autospec(
            SecondInstanceJudgmentDraftsRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.use_case = CreateSecondInstanceJudgmentDraftUseCase(
            judgment_drafts_repository=self.judgment_drafts_repository_mock,
            analyses_repository=self.analyses_repository_mock,
        )

    def test_should_add_judgment_draft_and_update_analysis_status_to_done(self) -> None:
        analysis_id = Id.create().value
        dto = self._create_judgment_draft_dto(analysis_id=Id.create().value)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_generating_judgment_draft().dto,
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.judgment_drafts_repository_mock.add.assert_called_once()
        self.judgment_drafts_repository_mock.replace.assert_not_called()
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)

        persisted_judgment_draft = (
            self.judgment_drafts_repository_mock.add.call_args.args[0]
        )

        assert persisted_judgment_draft == SecondInstanceJudgmentDraft.create(
            SecondInstanceJudgmentDraftDto(
                analysis_id=analysis_id,
                report=dto.report,
                merit_analysis=dto.merit_analysis,
                precedent_adherence_analysis=dto.precedent_adherence_analysis,
                ruling=dto.ruling,
                preliminary_issues=dto.preliminary_issues,
                no_applicable_precedent_notice=dto.no_applicable_precedent_notice,
            )
        )
        assert result == SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report=dto.report,
            merit_analysis=dto.merit_analysis,
            precedent_adherence_analysis=dto.precedent_adherence_analysis,
            ruling=dto.ruling,
            preliminary_issues=dto.preliminary_issues,
            no_applicable_precedent_notice=dto.no_applicable_precedent_notice,
        )
        assert analysis.status == SecondInstanceAnalysisStatus.create_as_done()

    def test_should_replace_judgment_draft_when_it_already_exists(self) -> None:
        analysis_id = Id.create().value
        dto = self._create_judgment_draft_dto(analysis_id=analysis_id)
        existing_judgment_draft = SecondInstanceJudgmentDraft.create(dto)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_generating_judgment_draft().dto,
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            existing_judgment_draft
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.judgment_drafts_repository_mock.add.assert_not_called()
        self.judgment_drafts_repository_mock.replace.assert_called_once_with(
            existing_judgment_draft
        )
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)

        assert result == dto
        assert analysis.status == SecondInstanceAnalysisStatus.create_as_done()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = self._create_judgment_draft_dto(analysis_id=analysis_id)
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_second_instance_analysis_required_error_when_analysis_is_not_second_instance(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = self._create_judgment_draft_dto(analysis_id=analysis_id)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_first_instance().dto,
            status='CASE_ANALYZED',
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(SecondInstanceAnalysisRequiredError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

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
                folder_id=None,
                account_id=Id.create().value,
                type=analysis_type,
                status=status,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )

    @staticmethod
    def _create_judgment_draft_dto(analysis_id: str) -> SecondInstanceJudgmentDraftDto:
        return SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report='Relatório',
            merit_analysis='Fundamentação',
            precedent_adherence_analysis='Aderência',
            ruling=['Dispositivo 1', 'Dispositivo 2'],
            preliminary_issues='Preliminar',
            no_applicable_precedent_notice='Aviso',
        )
