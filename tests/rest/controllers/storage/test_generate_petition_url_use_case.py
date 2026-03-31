from unittest.mock import MagicMock, create_autospec

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from animus.core.storage.domain.structures.dtos.upload_url_dto import UploadUrlDto
from animus.core.storage.interfaces.file_storage_provider import FileStorageProvider
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.providers_pipe import ProvidersPipe
from animus.rest.controllers.storage.generate_petition_upload_url_controller import (
    GeneratePetitionUploadUrlController,
)


class TestGeneratePetitionUploadUrlController:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.app = FastAPI()
        self.router = APIRouter()
        GeneratePetitionUploadUrlController.handle(self.router)
        self.app.include_router(self.router, prefix='/storage')

        self.client = TestClient(self.app)

        self.file_storage_provider_mock = create_autospec(
            FileStorageProvider, instance=True
        )
        self.app.dependency_overrides[ProvidersPipe.get_file_storage_provider] = (
            lambda: self.file_storage_provider_mock
        )
        self.app.dependency_overrides[
            IntakePipe.verify_analysis_by_account_from_request
        ] = lambda: MagicMock()

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_should_return_201_and_dto_when_request_is_valid(self) -> None:
        analysis_id = 'fake-analysis-123'
        document_type = 'pdf'
        expected_dto = UploadUrlDto(
            url='https://storage.googleapis.com/fake-url',
            token='fake-token',  # noqa: S106
            file_path=f'analyses/{analysis_id}/petitions/fake-ulid.{document_type}',
        )

        mock_upload_url = MagicMock()
        mock_upload_url.dto = expected_dto
        self.file_storage_provider_mock.generate_upload_url.return_value = (
            mock_upload_url
        )

        response = self.client.post(
            f'/storage/analyses/{analysis_id}/petitions/upload?document_type={document_type}'
        )

        assert response.status_code == 201
        assert response.json() == {
            'url': 'https://storage.googleapis.com/fake-url',
            'token': 'fake-token',
            'file_path': f'analyses/{analysis_id}/petitions/fake-ulid.{document_type}',
        }

    def test_should_return_422_when_document_type_is_invalid(self) -> None:
        response = self.client.post(
            '/storage/analyses/fake-analysis-123/petitions/upload?document_type=txt'
        )

        assert response.status_code == 422
        self.file_storage_provider_mock.generate_upload_url.assert_not_called()
