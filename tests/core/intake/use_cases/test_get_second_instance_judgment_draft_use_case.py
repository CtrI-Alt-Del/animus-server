from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import SecondInstanceJudgmentDraftUnavailableError
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.interfaces import SecondInstanceJudgmentDraftsRepository
from animus.core.intake.use_cases import GetSecondInstanceJudgmentDraftUseCase
from animus.core.shared.domain.structures import Id


class TestGetSecondInstanceJudgmentDraftUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.judgment_drafts_repository_mock = create_autospec(
            SecondInstanceJudgmentDraftsRepository,
            instance=True,
        )
        self.use_case = GetSecondInstanceJudgmentDraftUseCase(
            judgment_drafts_repository=self.judgment_drafts_repository_mock,
        )

    def test_should_return_judgment_draft_dto_when_draft_exists(self) -> None:
        analysis_id = Id.create().value
        judgment_draft = SecondInstanceJudgmentDraft.create(
            SecondInstanceJudgmentDraftDto(
                analysis_id=analysis_id,
                report='Relatório',
                merit_analysis='Fundamentacao',
                precedent_adherence_analysis='Aderência',
                ruling=['Item 1', 'Item 2'],
            )
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            judgment_draft
        )

        result = self.use_case.execute(analysis_id=analysis_id)

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        assert result == judgment_draft.dto

    def test_should_raise_error_when_draft_does_not_exist(self) -> None:
        analysis_id = Id.create().value
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(SecondInstanceJudgmentDraftUnavailableError):
            self.use_case.execute(analysis_id=analysis_id)
