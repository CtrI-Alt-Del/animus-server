from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis, AnalysisType
from animus.core.intake.domain.entities.dtos import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PetitionDraftUnavailableError,
)
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.intake.interfaces import AnalysesRepository, PetitionDraftsRepository
from animus.core.intake.use_cases import GetPetitionDraftUseCase
from animus.core.shared.domain.errors import ForbiddenError
from animus.core.shared.domain.structures import Id


def _make_analysis(*, analysis_id: str, account_id: str) -> Analysis:
    return Analysis.create(
        AnalysisDto(
            id=analysis_id,
            name='Análise',
            account_id=account_id,
            status='DONE',
            created_at='2026-05-26T10:00:00Z',
            type=AnalysisType.create_as_case_assessment().dto,
        )
    )


def _make_petition_draft(analysis_id: str) -> PetitionDraft:
    return PetitionDraft.create(
        PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts='Fatos estruturados',
            legal_grounds='Fundamentos jurídicos',
            central_thesis='Tese central',
            requests=['Pedido 1'],
            precedent_citations=['STJ REsp 123 - tese aplicável'],
        )
    )


class TestGetPetitionDraftUseCase:
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
        self.use_case = GetPetitionDraftUseCase(
            analyses_repository=self.analyses_repository_mock,
            petition_drafts_repository=self.petition_drafts_repository_mock,
        )

    def test_should_return_petition_draft_dto_when_draft_exists(self) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = _make_analysis(analysis_id=analysis_id, account_id=account_id)
        petition_draft = _make_petition_draft(analysis_id)
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            petition_draft
        )

        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        assert result == petition_draft.dto

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_not_called()

    def test_should_raise_forbidden_error_when_analysis_belongs_to_another_account(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = _make_analysis(
            analysis_id=analysis_id,
            account_id=Id.create().value,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(ForbiddenError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_not_called()

    def test_should_raise_petition_draft_unavailable_error_when_draft_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = _make_analysis(analysis_id=analysis_id, account_id=account_id)
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(PetitionDraftUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)
