from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.entities.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.entities.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.errors import (
    AnalysisDocumentNotFoundError,
    AnalysisNotFoundError,
)
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalisysesRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import CreateCaseSummaryUseCase
from animus.core.shared.domain.structures import Id


def _make_case_summary_dto() -> CaseSummaryDto:
    return CaseSummaryDto(
        case_summary='Resumo do caso',
        legal_issue='Questao juridica',
        central_question='Pergunta central',
        relevant_laws=['Lei 1'],
        key_facts=['Fato 1'],
        search_terms=['termo 1'],
    )


class TestCreateCaseSummaryUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository,
            instance=True,
        )
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository,
            instance=True,
        )
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = CreateCaseSummaryUseCase(
            case_summaries_repository=self.case_summaries_repository_mock,
            analysis_documents_repository=self.analysis_documents_repository_mock,
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_add_case_summary_and_update_case_assessment_status(self) -> None:
        analysis_id = Id.create().value
        dto = _make_case_summary_dto()
        analysis_document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )
        )
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Analise',
                account_id=Id.create().value,
                status=CaseAssessmentAnalysisStatus.ANALYZING_CASE.value,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.CASE_ASSESSMENT,
            )
        )

        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            analysis_document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.case_summaries_repository_mock.add.assert_called_once()
        self.case_summaries_repository_mock.replace.assert_not_called()
        self.analisyses_repository_mock.replace.assert_called_once()

        updated_analysis = self.analisyses_repository_mock.replace.call_args.args[0]

        assert result == CaseSummary.create(dto).dto
        assert (
            updated_analysis.status == CaseAssessmentAnalysisStatus.CASE_ANALYZED.value
        )

    def test_should_replace_case_summary_and_update_second_instance_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = _make_case_summary_dto()
        analysis_document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )
        )
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Analise',
                account_id=Id.create().value,
                status=SecondInstanceAnalysisStatus.ANALYZING_CASE.value,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.SECOND_INSTANCE,
            )
        )

        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            analysis_document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = object()
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.case_summaries_repository_mock.add.assert_not_called()
        self.case_summaries_repository_mock.replace.assert_called_once()
        self.analisyses_repository_mock.replace.assert_called_once()

        updated_analysis = self.analisyses_repository_mock.replace.call_args.args[0]

        assert result == CaseSummary.create(dto).dto
        assert (
            updated_analysis.status == SecondInstanceAnalysisStatus.CASE_ANALYZED.value
        )

    def test_should_raise_analysis_document_not_found_error_when_document_does_not_exist(
        self,
    ) -> None:
        dto = _make_case_summary_dto()
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(AnalysisDocumentNotFoundError):
            self.use_case.execute(analysis_id=Id.create().value, dto=dto)

        self.case_summaries_repository_mock.add.assert_not_called()
        self.case_summaries_repository_mock.replace.assert_not_called()
        self.analisyses_repository_mock.replace.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = _make_case_summary_dto()
        analysis_document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )
        )
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            analysis_document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None
        self.analisyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.analisyses_repository_mock.replace.assert_not_called()
