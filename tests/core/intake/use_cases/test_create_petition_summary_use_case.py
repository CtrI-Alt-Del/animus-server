from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.structures.dtos import PetitionSummaryDto
from animus.core.intake.interfaces import PetitionSummariesRepository
from animus.core.intake.use_cases import CreatePetitionSummaryUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id


class TestCreatePetitionSummaryUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petition_summaries_repository_mock = create_autospec(
            PetitionSummariesRepository,
            instance=True,
        )
        self.use_case = CreatePetitionSummaryUseCase(
            petition_summaries_repository=self.petition_summaries_repository_mock,
        )

    def test_should_add_petition_summary_when_petition_does_not_have_summary(
        self,
    ) -> None:
        petition_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        dto = PetitionSummaryDto(
            content='Resumo da peticao inicial com os fatos centrais.',
            main_points=[
                'A autora relata descumprimento contratual.',
                'A peticao aponta fundamento no CDC.',
                'Ha pedido de indenizacao por danos materiais.',
            ],
        )
        petition_id_entity = Id.create(petition_id)

        self.petition_summaries_repository_mock.find_by_petition_id.return_value = None

        result = self.use_case.execute(petition_id=petition_id, dto=dto)

        self.petition_summaries_repository_mock.find_by_petition_id.assert_called_once_with(
            petition_id=petition_id_entity,
        )
        self.petition_summaries_repository_mock.add.assert_called_once()
        self.petition_summaries_repository_mock.replace.assert_not_called()
        petition_summary = self.petition_summaries_repository_mock.add.call_args.kwargs[
            'petition_summary'
        ]
        assert (
            self.petition_summaries_repository_mock.add.call_args.kwargs['petition_id']
            == petition_id_entity
        )
        assert petition_summary.dto == dto
        assert result == dto

    def test_should_replace_petition_summary_when_petition_already_has_summary(
        self,
    ) -> None:
        petition_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        dto = PetitionSummaryDto(
            content='Novo resumo consolidado da peticao.',
            main_points=[
                'Os fatos foram reorganizados cronologicamente.',
                'O fundamento juridico foi reforcado com jurisprudencia.',
                'O pedido principal foi mantido com tutela de urgencia.',
            ],
        )
        petition_id_entity = Id.create(petition_id)
        self.petition_summaries_repository_mock.find_by_petition_id.return_value = (
            object()
        )

        result = self.use_case.execute(petition_id=petition_id, dto=dto)

        self.petition_summaries_repository_mock.find_by_petition_id.assert_called_once_with(
            petition_id=petition_id_entity,
        )
        self.petition_summaries_repository_mock.add.assert_not_called()
        self.petition_summaries_repository_mock.replace.assert_called_once()
        petition_summary = (
            self.petition_summaries_repository_mock.replace.call_args.kwargs[
                'petition_summary'
            ]
        )
        assert (
            self.petition_summaries_repository_mock.replace.call_args.kwargs[
                'petition_id'
            ]
            == petition_id_entity
        )
        assert petition_summary.dto == dto
        assert result == dto

    def test_should_raise_validation_error_when_petition_id_is_invalid(self) -> None:
        dto = PetitionSummaryDto(
            content='Resumo valido.',
            main_points=['Ponto principal.'],
        )

        with pytest.raises(ValidationError):
            self.use_case.execute(petition_id='invalid-petition-id', dto=dto)

        self.petition_summaries_repository_mock.find_by_petition_id.assert_not_called()
        self.petition_summaries_repository_mock.add.assert_not_called()
        self.petition_summaries_repository_mock.replace.assert_not_called()
