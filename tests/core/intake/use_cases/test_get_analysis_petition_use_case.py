from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.errors import PetitionNotFoundError
from animus.core.intake.interfaces import PetitionsRepository
from animus.core.intake.use_cases.get_analysis_petition_use_case import (
    GetAnalysisPetitionUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.entities.petitions_faker import PetitionsFaker


class TestGetAnalysisPetitionUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petitions_repository_mock = create_autospec(
            PetitionsRepository,
            instance=True,
        )
        self.use_case = GetAnalysisPetitionUseCase(
            petitions_repository=self.petitions_repository_mock,
        )

    def test_should_return_petition_dto_when_analysis_has_a_petition(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        petition = PetitionsFaker.fake(
            petition_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
            analysis_id=analysis_id,
            document=PetitionDocumentDto(
                file_path='petitions/analysis-petition.pdf',
                name='analysis-petition.pdf',
            ),
        )
        self.petitions_repository_mock.find_by_analysis_id.return_value = petition

        result = self.use_case.execute(analysis_id=analysis_id)

        self.petitions_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        assert result == petition.dto

    def test_should_raise_petition_not_found_error_when_analysis_does_not_have_a_petition(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        self.petitions_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(PetitionNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.petitions_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
