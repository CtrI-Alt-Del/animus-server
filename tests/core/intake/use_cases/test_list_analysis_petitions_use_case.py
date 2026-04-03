from unittest.mock import call, create_autospec

import pytest

from animus.core.intake.domain.entities import Petition
from animus.core.intake.domain.entities.dtos import PetitionDocumentDto, PetitionDto
from animus.core.intake.domain.structures import PetitionSummary
from animus.core.intake.domain.structures.dtos import (
    AnalysisPetitionDto,
    PetitionSummaryDto,
)
from animus.core.intake.interfaces import (
    PetitionSummariesRepository,
    PetitionsRepository,
)
from animus.core.intake.use_cases import ListAnalysisPetitionsUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class TestListAnalysisPetitionsUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petitions_repository_mock = create_autospec(
            PetitionsRepository,
            instance=True,
        )
        self.petition_summaries_repository_mock = create_autospec(
            PetitionSummariesRepository,
            instance=True,
        )
        self.use_case = ListAnalysisPetitionsUseCase(
            petitions_repository=self.petitions_repository_mock,
            petition_summaries_repository=self.petition_summaries_repository_mock,
        )

    def test_should_list_analysis_petitions_with_their_summaries_when_analysis_exists(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        first_petition = Petition.create(
            PetitionDto(
                id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                document=PetitionDocumentDto(
                    file_path='petitions/first-petition.pdf',
                    name='first-petition.pdf',
                ),
            )
        )
        second_petition = Petition.create(
            PetitionDto(
                id='01B3EAF4Q2V7D9N8M6K5J4H3G3',
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T11:30:00+00:00',
                document=PetitionDocumentDto(
                    file_path='petitions/second-petition.pdf',
                    name='second-petition.pdf',
                ),
            )
        )
        first_summary = PetitionSummary.create(
            PetitionSummaryDto(
                case_summary='Resumo da primeira peticao.',
                legal_issue='Questao juridica da primeira peticao.',
                central_question='A primeira pretensao tem amparo legal?',
                relevant_laws=['Codigo Civil, Art. 186'],
                key_facts=['Fato relevante da primeira peticao.'],
                search_terms=['responsabilidade civil'],
            )
        )

        self.petitions_repository_mock.find_all_by_analysis_id_ordered_by_uploaded_at.return_value = ListResponse(
            items=[first_petition, second_petition]
        )
        self.petition_summaries_repository_mock.find_by_petition_id.side_effect = [
            first_summary,
            None,
        ]

        result = self.use_case.execute(analysis_id=analysis_id)

        self.petitions_repository_mock.find_all_by_analysis_id_ordered_by_uploaded_at.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        self.petition_summaries_repository_mock.find_by_petition_id.assert_has_calls(
            [call(first_petition.id), call(second_petition.id)]
        )
        assert (
            self.petition_summaries_repository_mock.find_by_petition_id.call_count == 2
        )
        assert result == ListResponse(
            items=[
                AnalysisPetitionDto(
                    petition=first_petition.dto,
                    summary=first_summary.dto,
                ),
                AnalysisPetitionDto(
                    petition=second_petition.dto,
                    summary=None,
                ),
            ]
        )

    def test_should_raise_validation_error_when_analysis_id_is_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(analysis_id='invalid-analysis-id')

        self.petitions_repository_mock.find_all_by_analysis_id_ordered_by_uploaded_at.assert_not_called()
        self.petition_summaries_repository_mock.find_by_petition_id.assert_not_called()
