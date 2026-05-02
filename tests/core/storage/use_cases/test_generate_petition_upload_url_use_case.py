from unittest.mock import create_autospec, patch

import pytest

from animus.core.shared.domain.structures import FilePath, Text
from animus.core.storage.domain.structures import UploadUrl
from animus.core.storage.domain.structures.url import Url
from animus.core.storage.interfaces import FileStorageProvider
from animus.core.storage.use_cases.generate_petition_upload_url_use_case import (
    GeneratePetitionUploadUrlUseCase,
)


class TestGeneratePetitionUploadUrlUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.file_storage_provider_mock = create_autospec(
            FileStorageProvider,
            instance=True,
        )
        self.use_case = GeneratePetitionUploadUrlUseCase(
            file_storage_provider=self.file_storage_provider_mock,
        )
        self.mock_file_path = FilePath.create('analyses/123/petitions/fake-ulid.pdf')
        self.mock_upload_url = UploadUrl.create(
            url=Url.create('https://storage.googleapis.com/signed-url'),
            token=Text.create('fake-token'),
            file_path=self.mock_file_path,
        )

    @patch('animus.core.storage.use_cases.generate_petition_upload_url_use_case.Id')
    def test_should_generate_upload_url_for_pdf_document(self, mock_id) -> None:  # noqa:ANN001 # type:ignore
        class FakeId:
            value = 'FAKE_ULID_123'

        mock_id.create.return_value = FakeId()  # type:ignore

        analysis_id = 'analysis-abc'
        document_type = 'pdf'

        expected_raw_path = (
            f'intake/analyses/{analysis_id}/petitions/FAKE_ULID_123.{document_type}'
        )
        expected_file_path = FilePath.create(expected_raw_path)

        expected_upload_url_response = UploadUrl.create(
            url=Url.create('https://storage.googleapis.com/signed-url-pdf'),
            token=Text.create(''),
            file_path=expected_file_path,
        )
        self.file_storage_provider_mock.generate_upload_url.return_value = (
            expected_upload_url_response
        )

        result = self.use_case.execute(
            analysis_id=analysis_id, document_type=document_type
        )
        self.file_storage_provider_mock.generate_upload_url.assert_called_once_with(
            file_path=expected_file_path
        )
        assert result == expected_upload_url_response.dto

    @patch('animus.core.storage.use_cases.generate_petition_upload_url_use_case.Id')
    def test_should_generate_upload_url_for_docx_document(self, mock_id) -> None:  # noqa:ANN001 # type:ignore
        class FakeId:
            value = 'FAKE_ULID_DOCX'

        mock_id.create.return_value = FakeId()  # type:ignore

        analysis_id = 'analysis-xyz'
        document_type = 'docx'
        expected_raw_path = (
            f'intake/analyses/{analysis_id}/petitions/FAKE_ULID_DOCX.{document_type}'
        )
        expected_file_path = FilePath.create(expected_raw_path)

        expected_upload_url_response = UploadUrl.create(
            url=Url.create('https://storage.googleapis.com/signed-url-docx'),
            token=Text.create(''),
            file_path=expected_file_path,
        )
        self.file_storage_provider_mock.generate_upload_url.return_value = (
            expected_upload_url_response
        )
        result = self.use_case.execute(
            analysis_id=analysis_id, document_type=document_type
        )
        self.file_storage_provider_mock.generate_upload_url.assert_called_once_with(
            file_path=expected_file_path
        )
        assert result == expected_upload_url_response.dto
