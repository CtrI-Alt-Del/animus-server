import time
from typing import Any

import pytest
from pytest import MonkeyPatch

from animus.providers.notification.email_sender.resend.resend_email_sender_provider import (
    ResendEmailSenderProvider,
)


class TestSendAccountVerificationEmailJob:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_event_with_real_inngest_dev_server(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
    ) -> None:
        captured_calls: list[dict[str, str]] = []

        def _send_account_verification_email(
            _self: ResendEmailSenderProvider,
            *,
            account_email: Any,
            verification_token: Any,
        ) -> None:
            captured_calls.append(
                {
                    'account_email': account_email.value,
                    'verification_token': verification_token.value,
                }
            )

        monkeypatch.setattr(
            ResendEmailSenderProvider,
            'send_account_verification_email',
            _send_account_verification_email,
        )
        response = inngest_runtime.post_event(
            name='auth/email-verification.requested',
            data={
                'account_email': 'maria@example.com',
                'account_email_verification_token': 'verification-token',
            },
        )

        assert response.status == 200

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if len(captured_calls) == 1:
                break
            time.sleep(0.1)
        else:
            msg = 'condition not satisfied before timeout'
            raise AssertionError(msg)

        assert captured_calls == [
            {
                'account_email': 'maria@example.com',
                'verification_token': 'verification-token',
            }
        ]
