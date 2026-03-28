from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import (
    PetitionDocumentNotFoundError,
    UnreadablePetitionDocumentError,
    UnsupportedPetitionDocumentTypeError,
)
from animus.core.shared.domain.structures import Decimal, Text
from animus.core.storage.domain.structures import File
from animus.core.storage.interfaces import (
    DocxProvider,
    FileStorageProvider,
    PdfProvider,
)
from animus.core.storage.use_cases import GetDocumentContentUseCase


class NotFoundWithCodeError(Exception):
    code = 404


NotFound = type('NotFound', (Exception,), {})


class TestGetDocumentContentUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.file_storage_provider_mock = create_autospec(
            FileStorageProvider,
            instance=True,
        )
        self.pdf_provider_mock = create_autospec(PdfProvider, instance=True)
        self.docx_provider_mock = create_autospec(DocxProvider, instance=True)
        self.use_case = GetDocumentContentUseCase(
            file_storage_provider=self.file_storage_provider_mock,
            pdf_provider=self.pdf_provider_mock,
            docx_provider=self.docx_provider_mock,
        )

        self.pdf_file = File.create(
            value=b'%PDF-1.4',
            key=Text.create('petitions/sample.pdf'),
            size_in_bytes=Decimal.create(0.5),
            mime_type=Text.create('application/pdf'),
        )
        self.docx_file = File.create(
            value=b'docx-bytes',
            key=Text.create('petitions/sample.docx'),
            size_in_bytes=Decimal.create(0.5),
            mime_type=Text.create(
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ),
        )

    def test_should_return_pdf_content_when_file_is_pdf(self) -> None:
        file_path = 'petitions/sample.pdf'
        expected_content = Text.create('Conteudo da peticao em PDF')
        self.file_storage_provider_mock.get_file.return_value = self.pdf_file
        self.pdf_provider_mock.extract_content.return_value = expected_content

        result = self.use_case.execute(file_path=file_path)

        self.file_storage_provider_mock.get_file.assert_called_once_with(
            Text.create(file_path)
        )
        self.pdf_provider_mock.extract_content.assert_called_once_with(self.pdf_file)
        self.docx_provider_mock.extract_content.assert_not_called()
        assert result == expected_content

    def test_should_return_docx_content_when_file_is_docx(self) -> None:
        file_path = 'petitions/sample.docx'
        expected_content = Text.create('Conteudo da peticao em DOCX')
        self.file_storage_provider_mock.get_file.return_value = self.docx_file
        self.docx_provider_mock.extract_content.return_value = expected_content

        result = self.use_case.execute(file_path=file_path)

        self.file_storage_provider_mock.get_file.assert_called_once_with(
            Text.create(file_path)
        )
        self.docx_provider_mock.extract_content.assert_called_once_with(self.docx_file)
        self.pdf_provider_mock.extract_content.assert_not_called()
        assert result == expected_content

    def test_should_raise_unsupported_document_type_error_when_extension_is_invalid(
        self,
    ) -> None:
        with pytest.raises(UnsupportedPetitionDocumentTypeError):
            self.use_case.execute(file_path='petitions/sample.txt')

        self.file_storage_provider_mock.get_file.assert_not_called()
        self.pdf_provider_mock.extract_content.assert_not_called()
        self.docx_provider_mock.extract_content.assert_not_called()

    def test_should_raise_petition_document_not_found_error_when_storage_returns_404(
        self,
    ) -> None:
        self.file_storage_provider_mock.get_file.side_effect = NotFoundWithCodeError()

        with pytest.raises(PetitionDocumentNotFoundError):
            self.use_case.execute(file_path='petitions/missing.pdf')

        self.pdf_provider_mock.extract_content.assert_not_called()
        self.docx_provider_mock.extract_content.assert_not_called()

    def test_should_raise_petition_document_not_found_error_when_storage_raises_not_found_named_error(
        self,
    ) -> None:
        self.file_storage_provider_mock.get_file.side_effect = NotFound()

        with pytest.raises(PetitionDocumentNotFoundError):
            self.use_case.execute(file_path='petitions/missing.docx')

        self.pdf_provider_mock.extract_content.assert_not_called()
        self.docx_provider_mock.extract_content.assert_not_called()

    def test_should_raise_unreadable_petition_document_error_when_parser_fails(
        self,
    ) -> None:
        self.file_storage_provider_mock.get_file.return_value = self.pdf_file
        self.pdf_provider_mock.extract_content.side_effect = RuntimeError('corrupted')

        with pytest.raises(UnreadablePetitionDocumentError):
            self.use_case.execute(file_path='petitions/corrupted.pdf')

        self.pdf_provider_mock.extract_content.assert_called_once_with(self.pdf_file)
        self.docx_provider_mock.extract_content.assert_not_called()

    def test_should_raise_unreadable_petition_document_error_when_content_is_blank(
        self,
    ) -> None:
        self.file_storage_provider_mock.get_file.return_value = self.docx_file
        self.docx_provider_mock.extract_content.return_value = Text.create('   ')

        with pytest.raises(UnreadablePetitionDocumentError):
            self.use_case.execute(file_path='petitions/blank.docx')

        self.docx_provider_mock.extract_content.assert_called_once_with(self.docx_file)
        self.pdf_provider_mock.extract_content.assert_not_called()
