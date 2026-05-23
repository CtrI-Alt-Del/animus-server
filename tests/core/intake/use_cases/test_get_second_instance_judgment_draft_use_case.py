from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceAnalysisRequiredError,
    SecondInstanceJudgmentDraftUnavailableError,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import GetSecondInstanceJudgmentDraftUseCase
from animus.core.shared.domain.errors import ForbiddenError
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker


class TestGetSecondInstanceJudgmentDraftUseCase:
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
        self.use_case = GetSecondInstanceJudgmentDraftUseCase(
            analyses_repository=self.analyses_repository_mock,
            judgment_drafts_repository=self.judgment_drafts_repository_mock,
        )

    def test_should_return_judgment_draft_dto_when_draft_exists(self) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=account_id,
            type=AnalysisType.create_as_second_instance().dto,
            status='DONE',
        )
        judgment_draft = SecondInstanceJudgmentDraft.create(
            SecondInstanceJudgmentDraftDto(
                analysis_id=analysis_id,
                report='Relatório',
                merit_analysis='Fundamentacao',
                precedent_adherence_analysis='Aderência',
                ruling=['Item 1', 'Item 2'],
            )
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            judgment_draft
        )

        result = self.use_case.execute(
            analysis_id=analysis_id,
            account_id=account_id,
        )

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        assert result == judgment_draft.dto

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id,
            )

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_not_called()

    def test_should_raise_forbidden_error_when_analysis_belongs_to_another_account(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=Id.create().value,
            type=AnalysisType.create_as_second_instance().dto,
            status='DONE',
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(ForbiddenError):
            self.use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id,
            )

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_not_called()

    def test_should_raise_type_error_when_analysis_is_not_second_instance(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=account_id,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(SecondInstanceAnalysisRequiredError):
            self.use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id,
            )

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_not_called()

    def test_should_raise_error_when_draft_does_not_exist(self) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=account_id,
            type=AnalysisType.create_as_second_instance().dto,
            status='DONE',
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(SecondInstanceJudgmentDraftUnavailableError):
            self.use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id,
            )

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
