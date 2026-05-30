import time
from typing import Any

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.notification import OneSignalPushNotificationProvider


def _seed_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> dict[str, str]:
    analysis_id = Id.create().value
    account_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise de teste',
            account_id=account_id,
            folder_id=None,
            type=AnalysisType.create_as_first_instance().dto,
            status=FirstInstanceAnalysisStatus.create_as_case_analyzed().dto,
            is_archived=False,
        )
    )
    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
        'account_id': account_id,
        'analysis_type': AnalysisType.create_as_first_instance().dto,
    }


class TestNotificationJobs:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_case_summary_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_analysis(sqlalchemy_session_factory)
        captured_calls: list[dict[str, str]] = []

        def _send_case_summary_finished_message(
            _self: OneSignalPushNotificationProvider,
            recipient_id: Id,
            analysis_id: Id,
            analysis_type: str,
        ) -> None:
            captured_calls.append(
                {
                    'recipient_id': recipient_id.value,
                    'analysis_id': analysis_id.value,
                    'analysis_type': analysis_type,
                }
            )

        monkeypatch.setattr(
            OneSignalPushNotificationProvider,
            'send_case_summary_finished_message',
            _send_case_summary_finished_message,
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        response = inngest_runtime.post_event(
            name='intake/case_summary.finished',
            data={
                'analysis_id': seeded_data['analysis_id'],
                'account_id': seeded_data['account_id'],
                'analysis_type': seeded_data['analysis_type'],
            },
        )

        assert response.status == 200

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if len(captured_calls) >= 1:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert len(captured_calls) >= 1
        assert captured_calls[0] == {
            'recipient_id': seeded_data['account_id'],
            'analysis_id': seeded_data['analysis_id'],
            'analysis_type': seeded_data['analysis_type'],
        }

    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_petition_summary_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_analysis(sqlalchemy_session_factory)
        captured_calls: list[dict[str, str]] = []

        def _send_petition_summary_finished_message(
            _self: OneSignalPushNotificationProvider,
            recipient_id: Id,
            analysis_id: Id,
            analysis_type: str,
        ) -> None:
            captured_calls.append(
                {
                    'recipient_id': recipient_id.value,
                    'analysis_id': analysis_id.value,
                    'analysis_type': analysis_type,
                }
            )

        monkeypatch.setattr(
            OneSignalPushNotificationProvider,
            'send_petition_summary_finished_message',
            _send_petition_summary_finished_message,
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        response = inngest_runtime.post_event(
            name='intake/petition_summary.finished',
            data={
                'analysis_id': seeded_data['analysis_id'],
                'account_id': seeded_data['account_id'],
                'analysis_type': seeded_data['analysis_type'],
            },
        )

        assert response.status == 200

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if len(captured_calls) >= 1:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert len(captured_calls) >= 1
        assert captured_calls[0] == {
            'recipient_id': seeded_data['account_id'],
            'analysis_id': seeded_data['analysis_id'],
            'analysis_type': seeded_data['analysis_type'],
        }

    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_petition_draft_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_analysis(sqlalchemy_session_factory)
        captured_calls: list[dict[str, str]] = []

        def _send_petition_draft_finished_message(
            _self: OneSignalPushNotificationProvider,
            recipient_id: Id,
            analysis_id: Id,
            analysis_type: str,
        ) -> None:
            captured_calls.append(
                {
                    'recipient_id': recipient_id.value,
                    'analysis_id': analysis_id.value,
                    'analysis_type': analysis_type,
                }
            )

        monkeypatch.setattr(
            OneSignalPushNotificationProvider,
            'send_petition_draft_finished_message',
            _send_petition_draft_finished_message,
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        response = inngest_runtime.post_event(
            name='intake/petition_draft.generation.finished',
            data={
                'analysis_id': seeded_data['analysis_id'],
                'account_id': seeded_data['account_id'],
                'analysis_type': seeded_data['analysis_type'],
            },
        )

        assert response.status == 200

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if len(captured_calls) >= 1:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert len(captured_calls) >= 1
        assert captured_calls[0] == {
            'recipient_id': seeded_data['account_id'],
            'analysis_id': seeded_data['analysis_id'],
            'analysis_type': seeded_data['analysis_type'],
        }

    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_judgment_draft_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_analysis(sqlalchemy_session_factory)
        captured_calls: list[dict[str, str]] = []

        def _send_second_instance_judgment_draft_finished_message(
            _self: OneSignalPushNotificationProvider,
            recipient_id: Id,
            analysis_id: Id,
            analysis_type: str,
        ) -> None:
            captured_calls.append(
                {
                    'recipient_id': recipient_id.value,
                    'analysis_id': analysis_id.value,
                    'analysis_type': analysis_type,
                }
            )

        monkeypatch.setattr(
            OneSignalPushNotificationProvider,
            'send_second_instance_judgment_draft_finished_message',
            _send_second_instance_judgment_draft_finished_message,
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        response = inngest_runtime.post_event(
            name='intake/judgment_draft.generation.finished',
            data={
                'analysis_id': seeded_data['analysis_id'],
                'account_id': seeded_data['account_id'],
                'analysis_type': seeded_data['analysis_type'],
            },
        )

        assert response.status == 200

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if len(captured_calls) >= 1:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert len(captured_calls) >= 1
        assert captured_calls[0] == {
            'recipient_id': seeded_data['account_id'],
            'analysis_id': seeded_data['analysis_id'],
            'analysis_type': seeded_data['analysis_type'],
        }

    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_precedents_search_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_analysis(sqlalchemy_session_factory)
        captured_calls: list[dict[str, str]] = []

        def _send_precedents_search_finished_message(
            _self: OneSignalPushNotificationProvider,
            recipient_id: Id,
            analysis_id: Id,
            analysis_type: str,
        ) -> None:
            captured_calls.append(
                {
                    'recipient_id': recipient_id.value,
                    'analysis_id': analysis_id.value,
                    'analysis_type': analysis_type,
                }
            )

        monkeypatch.setattr(
            OneSignalPushNotificationProvider,
            'send_precedents_search_finished_message',
            _send_precedents_search_finished_message,
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        response = inngest_runtime.post_event(
            name='intake/precedents_search.finished',
            data={
                'analysis_id': seeded_data['analysis_id'],
                'account_id': seeded_data['account_id'],
                'analysis_type': seeded_data['analysis_type'],
            },
        )

        assert response.status == 200

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if len(captured_calls) >= 1:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert len(captured_calls) >= 1
        assert captured_calls[0] == {
            'recipient_id': seeded_data['account_id'],
            'analysis_id': seeded_data['analysis_id'],
            'analysis_type': seeded_data['analysis_type'],
        }
