from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import AnalysisDocumentNotFoundError
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import AnalysisDocumentsRepository
from animus.core.intake.use_cases.get_analysis_document_use_case import (
    GetAnalysisDocumentUseCase,
)
from animus.core.shared.domain.structures import Id


class TestGetAnalysisDocumentUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository,
            instance=True,
        )
        self.use_case = GetAnalysisDocumentUseCase(
            analysis_documents_repository=self.analysis_documents_repository_mock,
        )

    def test_should_return_analysis_document_dto_when_document_exists(self) -> None:
        analysis_id = Id.create().value
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

        result = self.use_case.execute(analysis_id=analysis_id)

        self.analysis_documents_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        assert result == analysis_document.dto

    def test_should_raise_analysis_document_not_found_error_when_document_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(AnalysisDocumentNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.analysis_documents_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
