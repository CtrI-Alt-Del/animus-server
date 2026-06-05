from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.intake.use_cases.create_analysis_use_case import CreateAnalysisUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Integer


class TestCreateAnalysisUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.use_case = CreateAnalysisUseCase(
            analyses_repository=self.analyses_repository_mock,
        )

    def test_should_create_analysis_with_generated_name_and_add_it_to_repository(
        self,
    ) -> None:
        self.analyses_repository_mock.find_next_generated_name_number.return_value = (
            Integer.create(3)
        )

        result = self.use_case.execute(
            account_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
        )

        self.analyses_repository_mock.find_next_generated_name_number.assert_called_once_with(
            Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        )
        self.analyses_repository_mock.add.assert_called_once()
        added_analysis = self.analyses_repository_mock.add.call_args.args[0]

        assert added_analysis.dto == result
        assert result.name == 'Nova analise #3'
        assert result.account_id == '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        assert result.folder_id == '01BX5ZZKBKACTAV9WEVGEMMVRZ'
        assert result.type == AnalysisType.create_as_first_instance().dto
        assert (
            result.status
            == FirstInstanceAnalysisStatus.create_as_waiting_document_upload().dto
        )
        assert result.is_archived is False
        assert result.id is not None

    def test_should_raise_validation_error_when_folder_id_is_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                folder_id='invalid-folder-id',
            )

        self.analyses_repository_mock.find_next_generated_name_number.assert_not_called()
        self.analyses_repository_mock.add.assert_not_called()

    def test_should_create_case_assessment_analysis_with_waiting_briefing_status(
        self,
    ) -> None:
        self.analyses_repository_mock.find_next_generated_name_number.return_value = (
            Integer.create(4)
        )

        result = self.use_case.execute(
            account_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            type=AnalysisType.create_as_case_assessment().dto,
        )

        assert result.type == AnalysisType.create_as_case_assessment().dto
        assert (
            result.status
            == CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto
        )
