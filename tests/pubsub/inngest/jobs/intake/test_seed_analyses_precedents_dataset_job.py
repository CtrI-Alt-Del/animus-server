import time
from typing import Any

import pytest
from pytest import MonkeyPatch

from animus.pubsub.inngest.jobs.intake.seed_analyses_precedents_dataset_job import (
    SeedAnalysesPrecedentsDatasetJob,
)


def _wait_until(predicate: Any, *, timeout_seconds: float = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)

    raise AssertionError('condition not satisfied before timeout')


class TestSeedAnalysesPrecedentsDatasetJob:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_all_document_files_with_real_inngest_dev_server(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
    ) -> None:
        captured_calls: list[tuple[str, str]] = []

        async def _resolve_account() -> str:
            return 'account-id'

        async def _list_document_files() -> list[str]:
            return ['file-a.pdf', 'file-b.pdf']

        async def _process_file(
            account_id: str,
            document_file_path: str,
        ) -> list[dict[str, Any]]:
            captured_calls.append((account_id, document_file_path))
            return []

        monkeypatch.setattr(
            SeedAnalysesPrecedentsDatasetJob,
            '_resolve_account',
            _resolve_account,
        )
        monkeypatch.setattr(
            SeedAnalysesPrecedentsDatasetJob,
            '_list_document_files',
            _list_document_files,
        )
        monkeypatch.setattr(
            SeedAnalysesPrecedentsDatasetJob,
            '_process_file',
            _process_file,
        )

        response = inngest_runtime.post_event(
            name='intake/seed-analyses-precedents-dataset.requested',
            data={},
        )

        assert response.status == 200

        _wait_until(lambda: len(captured_calls) == 2)

        assert captured_calls == [
            ('account-id', 'file-a.pdf'),
            ('account-id', 'file-b.pdf'),
        ]
