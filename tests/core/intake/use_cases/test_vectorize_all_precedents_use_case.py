from unittest.mock import MagicMock, create_autospec

import pytest

from animus.core.intake.interfaces import (
    PrecedentEmbeddingsProvider,
    PrecedentsEmbeddingsRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases.vectorize_all_precedents_use_case import (
    VectorizeAllPrecedentsUseCase,
)
from animus.core.shared.responses.page_pagination_response import PagePaginationResponse


class TestVectorizeAllPrecedentsUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.precedents_repository_mock = create_autospec(
            PrecedentsRepository,
            instance=True,
        )
        self.precedent_embeddings_provider_mock = create_autospec(
            PrecedentEmbeddingsProvider,
            instance=True,
        )
        self.precedents_embeddings_repository_mock = create_autospec(
            PrecedentsEmbeddingsRepository,
            instance=True,
        )

        self.use_case = VectorizeAllPrecedentsUseCase(
            precedents_repository=self.precedents_repository_mock,
            precedent_embeddings_provider=self.precedent_embeddings_provider_mock,
            precedents_embeddings_repository=self.precedents_embeddings_repository_mock,
        )

    def test_should_vectorize_all_precedents_from_page(self) -> None:
        precedents = [MagicMock(), MagicMock(), MagicMock()]
        embeddings = [MagicMock(), MagicMock()]
        self.precedents_repository_mock.find_page.return_value = PagePaginationResponse(
            items=precedents,
            total=3,
            page=1,
            page_size=10,
        )
        self.precedent_embeddings_provider_mock.generate.return_value = embeddings

        result = self.use_case.execute(page=1, page_size=10)

        self.precedents_repository_mock.find_page.assert_called_once_with(1, 10)
        self.precedent_embeddings_provider_mock.generate.assert_called_once_with(
            precedents
        )
        self.precedents_embeddings_repository_mock.add_many.assert_called_once_with(
            embeddings
        )
        assert result == 3

    def test_should_not_generate_embeddings_when_page_is_empty(self) -> None:
        self.precedents_repository_mock.find_page.return_value = PagePaginationResponse(
            items=[],
            total=0,
            page=1,
            page_size=10,
        )

        result = self.use_case.execute(page=1, page_size=10)

        self.precedent_embeddings_provider_mock.generate.assert_not_called()
        self.precedents_embeddings_repository_mock.add_many.assert_not_called()
        assert result == 0
