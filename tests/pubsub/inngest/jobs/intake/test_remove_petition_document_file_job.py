import time
from typing import Any

import pytest
from pytest import MonkeyPatch

from animus.providers.storage import SupabaseFileStorageProvider


class TestRemovePetitionDocumentFileJob:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_event_with_real_inngest_dev_server_when_petition_is_replaced(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
    ) -> None:
        expected_path = 'petitions/analysis-123/original-document.pdf'
        captured_calls: list[list[str]] = []

        def _remove_files(
            _self: SupabaseFileStorageProvider,
            file_paths: Any,
        ) -> None:
            captured_calls.append([file_path.value for file_path in file_paths])

        monkeypatch.setattr(
            SupabaseFileStorageProvider,
            'remove_files',
            _remove_files,
        )

        response = inngest_runtime.post_event(
            name='intake/petition.replaced',
            data={'petition_document_path': expected_path},
        )

        assert response.status == 200

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if len(captured_calls) == 1:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert captured_calls == [[expected_path]]
