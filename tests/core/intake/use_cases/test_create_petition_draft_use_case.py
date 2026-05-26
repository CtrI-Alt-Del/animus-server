from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.intake.interfaces import AnalysesRepository, PetitionDraftsRepository
from animus.core.intake.use_cases import CreatePetitionDraftUseCase
from animus.core.shared.domain.structures import Id


class TestCreatePetitionDraftUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petition_drafts_repository_mock = create_autospec(
            PetitionDraftsRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.use_case = CreatePetitionDraftUseCase(
            petition_drafts_repository=self.petition_drafts_repository_mock,
            analyses_repository=self.analyses_repository_mock,
        )

    def test_should_add_petition_draft_and_update_analysis_status_to_done(self) -> None:
        analysis_id = Id.create().value
        dto = self._create_petition_draft_dto(analysis_id=Id.create().value)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_generating_petition_draft().dto,
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.petition_drafts_repository_mock.add.assert_called_once()
        self.petition_drafts_repository_mock.replace.assert_not_called()
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)

        persisted_petition_draft = (
            self.petition_drafts_repository_mock.add.call_args.args[0]
        )

        assert persisted_petition_draft == PetitionDraft.create(
            PetitionDraftDto(
                analysis_id=analysis_id,
                structured_facts=dto.structured_facts,
                legal_grounds=dto.legal_grounds,
                central_thesis=dto.central_thesis,
                requests=dto.requests,
                precedent_citations=dto.precedent_citations,
            )
        )
        assert result == PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts=dto.structured_facts,
            legal_grounds=dto.legal_grounds,
            central_thesis=dto.central_thesis,
            requests=dto.requests,
            precedent_citations=dto.precedent_citations,
        )
        assert analysis.status == CaseAssessmentAnalysisStatus.create_as_done()

    def test_should_replace_petition_draft_when_it_already_exists(self) -> None:
        analysis_id = Id.create().value
        dto = self._create_petition_draft_dto(analysis_id=analysis_id)
        existing_petition_draft = PetitionDraft.create(dto)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_generating_petition_draft().dto,
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            existing_petition_draft
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.petition_drafts_repository_mock.add.assert_not_called()
        self.petition_drafts_repository_mock.replace.assert_called_once_with(
            existing_petition_draft
        )
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)

        assert result == dto
        assert analysis.status == CaseAssessmentAnalysisStatus.create_as_done()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = self._create_petition_draft_dto(analysis_id=analysis_id)
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_inconsistent_analysis_type_error_when_analysis_is_not_case_assessment(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = self._create_petition_draft_dto(analysis_id=analysis_id)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_first_instance().dto,
            status='CASE_ANALYZED',
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(InconsistentAnalysisTypeError):
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
    def _create_petition_draft_dto(analysis_id: str) -> PetitionDraftDto:
        return PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts='Fatos estruturados',
            legal_grounds='Fundamentos jurídicos',
            central_thesis='Tese central',
            requests=['Pedido 1', 'Pedido 2'],
            precedent_citations=['Citação 1'],
        )
