from unittest.mock import MagicMock, create_autospec

import pytest

from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.interfaces.pangea_service import PangeaService
from animus.core.intake.interfaces.precedent_embeddings_provider import (
    PrecedentEmbeddingsProvider,
)
from animus.core.intake.interfaces.precedents_embeddings_repository import (
    PrecedentsEmbeddingsRepository,
)
from animus.core.intake.interfaces.precedents_repository import PrecedentsRepository
from animus.core.intake.use_cases.vectorize_precedents_use_case import (
    VectorizePrecedentsUseCase,
)
from animus.core.shared.responses.page_pagination_response import PagePaginationResponse


class TestVectorizePrecedentsUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.pangea_service_mock = create_autospec(PangeaService, instance=True)
        self.precedents_repository_mock = create_autospec(
            PrecedentsRepository, instance=True
        )
        self.embeddings_provider_mock = create_autospec(
            PrecedentEmbeddingsProvider, instance=True
        )
        self.embeddings_repository_mock = create_autospec(
            PrecedentsEmbeddingsRepository, instance=True
        )

        self.use_case = VectorizePrecedentsUseCase(
            pangea_service=self.pangea_service_mock,
            precedents_repository=self.precedents_repository_mock,
            embeddings_provider=self.embeddings_provider_mock,
            embeddings_repository=self.embeddings_repository_mock,
        )

    def test_should_process_and_save_embeddings_when_all_precedents_are_new(
        self,
    ) -> None:
        page, page_size = 1, 10
        precedent_1 = self._create_precedent_mock('prec-1')
        precedent_2 = self._create_precedent_mock('prec-2')
        new_precedents = [precedent_1, precedent_2]
        generated_embeddings = [MagicMock(), MagicMock()]

        pangea_response = MagicMock(spec=PagePaginationResponse)
        pangea_response.items = new_precedents

        self.pangea_service_mock.fetch_precedents.return_value = pangea_response
        self.precedents_repository_mock.find_all_identifiers.return_value = [
            'existing-prec-1'
        ]
        self.embeddings_provider_mock.generate.return_value = generated_embeddings

        result = self.use_case.execute(page=page, page_size=page_size)

        self.pangea_service_mock.fetch_precedents.assert_called_once_with(
            page, page_size
        )
        self.precedents_repository_mock.find_all_identifiers.assert_called_once()
        self.precedents_repository_mock.add_many.assert_called_once_with(new_precedents)
        self.embeddings_provider_mock.generate.assert_called_once_with(new_precedents)
        self.embeddings_repository_mock.add_many.assert_called_once_with(
            generated_embeddings
        )
        assert result == pangea_response

    def test_should_only_process_new_precedents_when_some_already_exist(self) -> None:
        page, page_size = 1, 10
        existing_precedent = self._create_precedent_mock('prec-1')
        new_precedent = self._create_precedent_mock('prec-2')
        generated_embeddings = [MagicMock()]

        pangea_response = MagicMock(spec=PagePaginationResponse)
        pangea_response.items = [existing_precedent, new_precedent]

        self.pangea_service_mock.fetch_precedents.return_value = pangea_response
        self.precedents_repository_mock.find_all_identifiers.return_value = ['prec-1']
        self.embeddings_provider_mock.generate.return_value = generated_embeddings

        result = self.use_case.execute(page=page, page_size=page_size)

        self.precedents_repository_mock.add_many.assert_called_once_with(
            [new_precedent]
        )
        self.embeddings_provider_mock.generate.assert_called_once_with([new_precedent])
        self.embeddings_repository_mock.add_many.assert_called_once_with(
            generated_embeddings
        )
        assert result == pangea_response

    def test_should_not_save_anything_when_all_precedents_already_exist(self) -> None:
        page, page_size = 1, 10
        existing_precedent = self._create_precedent_mock('prec-1')

        pangea_response = MagicMock(spec=PagePaginationResponse)
        pangea_response.items = [existing_precedent]

        self.pangea_service_mock.fetch_precedents.return_value = pangea_response
        self.precedents_repository_mock.find_all_identifiers.return_value = ['prec-1']

        result = self.use_case.execute(page=page, page_size=page_size)

        self.precedents_repository_mock.add_many.assert_not_called()
        self.embeddings_provider_mock.generate.assert_not_called()
        self.embeddings_repository_mock.add_many.assert_not_called()
        assert result == pangea_response

    def test_should_not_save_anything_when_pangea_returns_no_items(self) -> None:
        page, page_size = 1, 10
        pangea_response = MagicMock(spec=PagePaginationResponse)
        pangea_response.items = []

        self.pangea_service_mock.fetch_precedents.return_value = pangea_response
        self.precedents_repository_mock.find_all_identifiers.return_value = ['prec-1']

        result = self.use_case.execute(page=page, page_size=page_size)

        self.precedents_repository_mock.add_many.assert_not_called()
        self.embeddings_provider_mock.generate.assert_not_called()
        self.embeddings_repository_mock.add_many.assert_not_called()
        assert result == pangea_response

    def _create_precedent_mock(self, identifier: str) -> MagicMock:
        precedent_mock = MagicMock(spec=Precedent)
        precedent_mock.identifier = identifier
        return precedent_mock
