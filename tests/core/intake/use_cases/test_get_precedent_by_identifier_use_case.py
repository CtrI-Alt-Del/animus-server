from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Precedent
from animus.core.intake.domain.entities.dtos import PrecedentDto
from animus.core.intake.domain.errors.precedent_not_found_error import (
    PrecedentNotFoundError,
)
from animus.core.intake.domain.structures.dtos import PrecedentIdentifierDto
from animus.core.intake.interfaces import PrecedentsRepository
from animus.core.intake.use_cases import GetPrecedentUseCase


class TestGetPrecedentUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.precedents_repository_mock = create_autospec(
            PrecedentsRepository,
            instance=True,
        )
        self.use_case = GetPrecedentUseCase(
            precedents_repository=self.precedents_repository_mock,
        )

    def test_should_return_precedent_when_identifier_exists(self) -> None:
        precedent_identifier = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        precedent_dto = PrecedentDto(
            id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
            identifier=precedent_identifier,
            status='vigente',
            enunciation='Enunciado do precedente',
            thesis='Tese do precedente',
            last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
        )
        precedent = Precedent.create(precedent_dto)

        self.precedents_repository_mock.find_by_identifier.return_value = precedent

        result = self.use_case.execute(
            precedent_identifier_dto=precedent_identifier,
        )

        self.precedents_repository_mock.find_by_identifier.assert_called_once()
        assert result == precedent_dto

    def test_should_raise_precedent_not_found_error_when_identifier_does_not_exist(
        self,
    ) -> None:
        self.precedents_repository_mock.find_by_identifier.return_value = None

        with pytest.raises(PrecedentNotFoundError):
            self.use_case.execute(
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court='STF',
                    kind='RG',
                    number=101,
                ),
            )
