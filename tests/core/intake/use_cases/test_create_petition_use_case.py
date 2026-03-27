from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.intake.use_cases.create_petition_use_case import CreatePetitionUseCase
from animus.core.shared.domain.errors import ValidationError


class TestCreatePetitionUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petitions_repository_mock = create_autospec(
            PetitionsRepository,
            instance=True,
        )
        self.use_case = CreatePetitionUseCase(
            petitions_repository=self.petitions_repository_mock,
        )

    def test_should_create_petition_and_add_it_to_repository(self) -> None:
        document = PetitionDocumentDto(
            file_path='petitions/initial-petition.pdf',
            name='Initial Petition.pdf',
        )

        result = self.use_case.execute(
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            uploaded_at='2026-03-31T10:30:00+00:00',
            document=document,
        )

        self.petitions_repository_mock.add.assert_called_once()
        added_petition = self.petitions_repository_mock.add.call_args.args[0]
        assert added_petition.dto == result
        assert result.id is not None
        assert result.analysis_id == '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        assert result.uploaded_at == '2026-03-31T10:30:00+00:00'
        assert result.document == document

    def test_should_raise_validation_error_when_analysis_id_is_invalid(self) -> None:
        document = PetitionDocumentDto(
            file_path='petitions/initial-petition.pdf',
            name='Initial Petition.pdf',
        )

        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(
                analysis_id='invalid-analysis-id',
                uploaded_at='2026-03-31T10:30:00+00:00',
                document=document,
            )

        self.petitions_repository_mock.add.assert_not_called()
