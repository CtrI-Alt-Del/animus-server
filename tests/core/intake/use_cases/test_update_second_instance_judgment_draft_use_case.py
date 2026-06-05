from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceAnalysisRequiredError,
    SecondInstanceJudgmentDraftUnavailableError,
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
from animus.core.intake.use_cases.update_second_instance_judgment_draft_use_case import (
    UpdateSecondInstanceJudgmentDraftUseCase,
)
from animus.core.shared.domain.structures import Id


class TestUpdateSecondInstanceJudgmentDraftUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.judgment_drafts_repository_mock = create_autospec(
            SecondInstanceJudgmentDraftsRepository,
            instance=True,
        )
        self.use_case = UpdateSecondInstanceJudgmentDraftUseCase(
            analyses_repository=self.analyses_repository_mock,
            judgment_drafts_repository=self.judgment_drafts_repository_mock,
        )

    def test_should_replace_judgment_draft_with_analysis_id_from_path_without_changing_analysis_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        dto = self._create_judgment_draft_dto(analysis_id=Id.create().value)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_generating_judgment_draft().dto,
        )
        existing_judgment_draft = SecondInstanceJudgmentDraft.create(
            self._create_judgment_draft_dto(
                analysis_id=analysis_id,
                report='Relatorio anterior',
                merit_analysis='Fundamentacao anterior',
                precedent_adherence_analysis='Aderencia anterior',
                ruling=['Dispositivo anterior'],
            )
        )
        previous_status = analysis.status
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            existing_judgment_draft
        )

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.judgment_drafts_repository_mock.replace.assert_called_once_with(
            SecondInstanceJudgmentDraft.create(
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
        )
        self.analyses_repository_mock.replace.assert_not_called()

        assert result == SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report=dto.report,
            merit_analysis=dto.merit_analysis,
            precedent_adherence_analysis=dto.precedent_adherence_analysis,
            ruling=dto.ruling,
            preliminary_issues=dto.preliminary_issues,
            no_applicable_precedent_notice=dto.no_applicable_precedent_notice,
        )
        assert analysis.status == previous_status

    def test_should_return_normalized_judgment_draft_when_input_contains_extra_whitespace(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = self._create_judgment_draft_dto(
            analysis_id=Id.create().value,
            report='  Relatorio atualizado  ',
            merit_analysis='  Fundamentacao atualizada  ',
            precedent_adherence_analysis='  Aderencia atualizada  ',
            ruling=['  Dispositivo 1  ', '  Dispositivo 2  '],
            preliminary_issues='  Preliminar atualizada  ',
            no_applicable_precedent_notice='  Aviso atualizado  ',
        )
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_done().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            SecondInstanceJudgmentDraft.create(
                self._create_judgment_draft_dto(analysis_id=analysis_id)
            )
        )

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.judgment_drafts_repository_mock.replace.assert_called_once_with(
            SecondInstanceJudgmentDraft.create(
                SecondInstanceJudgmentDraftDto(
                    analysis_id=analysis_id,
                    report='Relatorio atualizado',
                    merit_analysis='Fundamentacao atualizada',
                    precedent_adherence_analysis='Aderencia atualizada',
                    ruling=['Dispositivo 1', 'Dispositivo 2'],
                    preliminary_issues='Preliminar atualizada',
                    no_applicable_precedent_notice='Aviso atualizado',
                )
            )
        )
        assert result == SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report='Relatorio atualizado',
            merit_analysis='Fundamentacao atualizada',
            precedent_adherence_analysis='Aderencia atualizada',
            ruling=['Dispositivo 1', 'Dispositivo 2'],
            preliminary_issues='Preliminar atualizada',
            no_applicable_precedent_notice='Aviso atualizado',
        )

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = self._create_judgment_draft_dto(analysis_id=analysis_id)
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.judgment_drafts_repository_mock.replace.assert_not_called()
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
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(SecondInstanceAnalysisRequiredError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.judgment_drafts_repository_mock.replace.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_second_instance_judgment_draft_unavailable_error_when_judgment_draft_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        dto = self._create_judgment_draft_dto(analysis_id=analysis_id)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_done().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(SecondInstanceJudgmentDraftUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.judgment_drafts_repository_mock.replace.assert_not_called()
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
    def _create_judgment_draft_dto(
        analysis_id: str,
        report: str = 'Relatório atualizado',
        merit_analysis: str = 'Fundamentação atualizada',
        precedent_adherence_analysis: str = 'Aderência atualizada',
        ruling: list[str] | None = None,
        preliminary_issues: str | None = 'Preliminar atualizada',
        no_applicable_precedent_notice: str | None = 'Aviso atualizado',
    ) -> SecondInstanceJudgmentDraftDto:
        return SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report=report,
            merit_analysis=merit_analysis,
            precedent_adherence_analysis=precedent_adherence_analysis,
            ruling=ruling or ['Dispositivo 1', 'Dispositivo 2'],
            preliminary_issues=preliminary_issues,
            no_applicable_precedent_notice=no_applicable_precedent_notice,
        )
