from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    InconsistentAnalysisTypeError,
    PetitionDraftUnavailableError,
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
from animus.core.intake.use_cases.update_petition_draft_use_case import (
    UpdatePetitionDraftUseCase,
)
from animus.core.shared.domain.structures import Id


class TestUpdatePetitionDraftUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.petition_drafts_repository_mock = create_autospec(
            PetitionDraftsRepository,
            instance=True,
        )
        self.use_case = UpdatePetitionDraftUseCase(
            analyses_repository=self.analyses_repository_mock,
            petition_drafts_repository=self.petition_drafts_repository_mock,
        )

    def test_should_replace_petition_draft_with_analysis_id_from_path_without_changing_analysis_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        dto = self._create_petition_draft_dto(analysis_id=Id.create().value)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_done().dto,
        )
        existing_petition_draft = PetitionDraft.create(
            self._create_petition_draft_dto(
                analysis_id=analysis_id,
                structured_facts='Versao anterior',
                legal_grounds='Fundamentos anteriores',
                central_thesis='Tese anterior',
                requests=['Pedido anterior'],
                precedent_citations=['Citação anterior'],
            )
        )
        previous_status = analysis.status
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            existing_petition_draft
        )

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.petition_drafts_repository_mock.replace.assert_called_once_with(
            PetitionDraft.create(
                PetitionDraftDto(
                    analysis_id=analysis_id,
                    structured_facts=dto.structured_facts,
                    legal_grounds=dto.legal_grounds,
                    central_thesis=dto.central_thesis,
                    requests=dto.requests,
                    precedent_citations=dto.precedent_citations,
                )
            )
        )
        self.analyses_repository_mock.replace.assert_not_called()

        assert result == PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts=dto.structured_facts,
            legal_grounds=dto.legal_grounds,
            central_thesis=dto.central_thesis,
            requests=dto.requests,
            precedent_citations=dto.precedent_citations,
        )
        assert analysis.status == previous_status

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = self._create_petition_draft_dto(analysis_id=analysis_id)
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.petition_drafts_repository_mock.replace.assert_not_called()
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
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(InconsistentAnalysisTypeError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.petition_drafts_repository_mock.replace.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_petition_draft_unavailable_error_when_petition_draft_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        dto = self._create_petition_draft_dto(analysis_id=analysis_id)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_done().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(PetitionDraftUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.petition_drafts_repository_mock.replace.assert_not_called()
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
    def _create_petition_draft_dto(
        analysis_id: str,
        structured_facts: str = 'Fatos estruturados atualizados',
        legal_grounds: str = 'Fundamentos jurídicos atualizados',
        central_thesis: str = 'Tese central atualizada',
        requests: list[str] | None = None,
        precedent_citations: list[str] | None = None,
    ) -> PetitionDraftDto:
        return PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts=structured_facts,
            legal_grounds=legal_grounds,
            central_thesis=central_thesis,
            requests=requests or ['Pedido 1', 'Pedido 2'],
            precedent_citations=precedent_citations or ['Citação 1'],
        )
