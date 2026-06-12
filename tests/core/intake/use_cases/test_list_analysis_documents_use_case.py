from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import AnalysisDocumentsRepository
from animus.core.intake.use_cases.list_analysis_documents_use_case import (
    ListAnalysisDocumentsUseCase,
)
from animus.core.shared.domain.structures import Id


class TestListAnalysisDocumentsUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository,
            instance=True,
        )
        self.use_case = ListAnalysisDocumentsUseCase(
            analysis_documents_repository=self.analysis_documents_repository_mock,
        )

    def test_should_return_analysis_documents_dtos_when_documents_exist(self) -> None:
        analysis_id = Id.create().value
        analysis_documents = [
            AnalysisDocument.create(
                AnalysisDocumentDto(
                    analysis_id=analysis_id,
                    uploaded_at='2026-03-27T10:30:00+00:00',
                    file_path='intake/analyses/document-1.pdf',
                    name='document-1.pdf',
                )
            ),
            AnalysisDocument.create(
                AnalysisDocumentDto(
                    analysis_id=analysis_id,
                    uploaded_at='2026-03-28T10:30:00+00:00',
                    file_path='intake/analyses/document-2.pdf',
                    name='document-2.pdf',
                )
            ),
        ]
        self.analysis_documents_repository_mock.find_many_by_analysis_id.return_value = analysis_documents

        result = self.use_case.execute(analysis_id=analysis_id)

        self.analysis_documents_repository_mock.find_many_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        assert result == [
            analysis_document.dto for analysis_document in analysis_documents
        ]

    def test_should_return_empty_list_when_documents_do_not_exist(self) -> None:
        analysis_id = Id.create().value
        self.analysis_documents_repository_mock.find_many_by_analysis_id.return_value = []

        result = self.use_case.execute(analysis_id=analysis_id)

        self.analysis_documents_repository_mock.find_many_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        assert result == []
