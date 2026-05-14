from unittest.mock import create_autospec

import pytest

from animus.core.intake.interfaces import ExtractedPetitionsRepository
from animus.core.intake.use_cases import CreateExtractedPetitionUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id


class TestCreateExtractedPetitionUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.extracted_petitions_repository_mock = create_autospec(
            ExtractedPetitionsRepository,
            instance=True,
        )
        self.use_case = CreateExtractedPetitionUseCase(
            extracted_petitions_repository=self.extracted_petitions_repository_mock,
        )

    def test_should_add_extracted_petition_when_cache_does_not_exist(self) -> None:
        analysis_id = Id.create().value
        self.extracted_petitions_repository_mock.find_by_analysis_id.return_value = None

        result = self.use_case.execute(
            analysis_id=analysis_id,
            first_page=3,
            last_page=9,
        )

        self.extracted_petitions_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        self.extracted_petitions_repository_mock.add.assert_called_once()
        self.extracted_petitions_repository_mock.replace.assert_not_called()

        added_extracted_petition = (
            self.extracted_petitions_repository_mock.add.call_args.args[0]
        )

        assert added_extracted_petition.dto == result
        assert result.analysis_id == analysis_id
        assert result.first_page == 3
        assert result.last_page == 9

    def test_should_replace_extracted_petition_when_cache_already_exists(self) -> None:
        analysis_id = Id.create().value
        self.extracted_petitions_repository_mock.find_by_analysis_id.return_value = (
            object()
        )

        result = self.use_case.execute(
            analysis_id=analysis_id,
            first_page=5,
            last_page=11,
        )

        self.extracted_petitions_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        self.extracted_petitions_repository_mock.add.assert_not_called()
        self.extracted_petitions_repository_mock.replace.assert_called_once()

        replaced_extracted_petition = (
            self.extracted_petitions_repository_mock.replace.call_args.args[0]
        )

        assert replaced_extracted_petition.dto == result
        assert result.analysis_id == analysis_id
        assert result.first_page == 5
        assert result.last_page == 11

    def test_should_raise_validation_error_when_first_page_is_less_than_one(
        self,
    ) -> None:
        with pytest.raises(
            ValidationError,
            match='Primeira pagina da peticao deve ser maior ou igual a 1',
        ):
            self.use_case.execute(
                analysis_id=Id.create().value,
                first_page=0,
                last_page=4,
            )

        self.extracted_petitions_repository_mock.find_by_analysis_id.assert_not_called()
        self.extracted_petitions_repository_mock.add.assert_not_called()
        self.extracted_petitions_repository_mock.replace.assert_not_called()
