import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest import MonkeyPatch

from animus.core.intake.use_cases.vectorize_all_precedents_use_case import (
    VectorizeAllPrecedentsUseCase,
)
from animus.database.qdrant.qdrant_precedents_embeddings_repository import (
    QdrantPrecedentsEmbeddingsRepository,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.intake.precedent_embeddings.openai.openai_precedent_embeddings_provider import (
    OpenAIPrecedentEmbeddingsProvider,
)


class TestVectorizeAllPrecedentsJob:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_existing_precedents_until_last_partial_page(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
    ) -> None:
        captured_calls: list[dict[str, int]] = []

        monkeypatch.setattr(
            QdrantPrecedentsEmbeddingsRepository,
            '__init__',
            lambda *args, **kwargs: None,  # type:ignore
        )
        monkeypatch.setattr(
            OpenAIPrecedentEmbeddingsProvider,
            '__init__',
            lambda *args, **kwargs: None,  # type:ignore
        )

        def _execute(
            _self: Any,
            *,
            page: int,
            page_size: int,
        ) -> int:
            captured_calls.append(
                {
                    'page': page,
                    'page_size': page_size,
                }
            )
            return 100 if page < 3 else 4

        monkeypatch.setattr(
            VectorizeAllPrecedentsUseCase,
            'execute',
            _execute,
        )

        mock_session_cm = MagicMock()
        mock_session_cm.__enter__.return_value = MagicMock()
        monkeypatch.setattr(
            Sqlalchemy,
            'session',
            lambda: mock_session_cm,
        )

        response = inngest_runtime.post_event(
            name='intake/vectorize-all-precedents.requested',
            data={},
        )

        assert response.status == 200

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if len(captured_calls) == 3:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert captured_calls == [
            {
                'page': 1,
                'page_size': 100,
            },
            {
                'page': 2,
                'page_size': 100,
            },
            {
                'page': 3,
                'page_size': 100,
            },
        ]
