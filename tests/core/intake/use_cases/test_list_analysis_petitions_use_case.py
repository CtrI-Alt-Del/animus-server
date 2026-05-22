from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.structures import AnalysisDocument, CaseSummary
from animus.core.intake.domain.structures.dtos import (
    AnalysisDocumentDto,
    AnalysisPetitionDto,
    CaseSummaryDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import ListAnalysisPetitionsUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class TestListAnalysisPetitionsUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository,
            instance=True,
        )
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository,
            instance=True,
        )
        self.use_case = ListAnalysisPetitionsUseCase(
            analysis_documents_repository=self.analysis_documents_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
        )

    def test_should_list_analysis_petitions_with_their_summaries_when_analysis_exists(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='documents/first-petition.pdf',
                name='first-petition.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo da primeira petição.',
                legal_issue='Questão juridica da primeira petição.',
                central_question='A primeira pretensao tem amparo legal?',
                relevant_laws=['Codigo Civil, Art. 186'],
                key_facts=['Fato relevante da primeira petição.'],
                search_terms=['responsabilidade civil'],
            )
        )

        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )

        result = self.use_case.execute(analysis_id=analysis_id)

        self.analysis_documents_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        assert result == ListResponse(
            items=[
                AnalysisPetitionDto(
                    document=document.dto,
                    case_summary=case_summary.dto,
                ),
            ]
        )

    def test_should_raise_validation_error_when_analysis_id_is_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(analysis_id='invalid-analysis-id')

        self.analysis_documents_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
