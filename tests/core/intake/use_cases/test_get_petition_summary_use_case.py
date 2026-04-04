from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import PetitionSummaryUnavailableError
from animus.core.intake.interfaces import PetitionSummariesRepository
from animus.core.intake.use_cases.get_petition_summary_use_case import (
    GetPetitionSummaryUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.structures.petition_summaries_faker import (
    PetitionSummariesFaker,
)


class TestGetPetitionSummaryUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petition_summaries_repository_mock = create_autospec(
            PetitionSummariesRepository,
            instance=True,
        )
        self.use_case = GetPetitionSummaryUseCase(
            petition_summaries_repository=self.petition_summaries_repository_mock,
        )

    def test_should_return_petition_summary_dto_when_summary_exists(self) -> None:
        petition_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        petition_summary = PetitionSummariesFaker.fake(
            case_summary='Resumo consolidado da peticao.',
            legal_issue='Discussao sobre inadimplemento contratual.',
            central_question='Existe responsabilidade contratual no caso?',
            relevant_laws=['Codigo Civil, Art. 389'],
            key_facts=['A autora relata inadimplemento contratual.'],
            search_terms=['inadimplemento contratual'],
        )

        self.petition_summaries_repository_mock.find_by_petition_id.return_value = (
            petition_summary
        )

        result = self.use_case.execute(petition_id=petition_id)

        self.petition_summaries_repository_mock.find_by_petition_id.assert_called_once_with(
            petition_id=Id.create(petition_id),
        )
        assert result == petition_summary.dto

    def test_should_raise_petition_summary_unavailable_error_when_summary_does_not_exist(
        self,
    ) -> None:
        petition_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        self.petition_summaries_repository_mock.find_by_petition_id.return_value = None

        with pytest.raises(PetitionSummaryUnavailableError):
            self.use_case.execute(petition_id=petition_id)

        self.petition_summaries_repository_mock.find_by_petition_id.assert_called_once_with(
            petition_id=Id.create(petition_id),
        )
