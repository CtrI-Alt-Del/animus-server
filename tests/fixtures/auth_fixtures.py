from collections.abc import Callable, Iterator
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.constants import Env
from animus.database.sqlalchemy.models.auth import AccountModel
from animus.providers.auth.email_verification.itsdangerous_email_verification_provider import (
    ItsdangerousEmailVerificationProvider,
)

CreateAccountFixture = Callable[..., AccountModel]


@pytest.fixture(autouse=True)
def auth_test_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    invalidated_tokens: set[str] = set()

    monkeypatch.setattr(Env, 'JWT_SECRET_KEY', 'test-jwt-secret')
    monkeypatch.setattr(Env, 'EMAIL_VERIFICATION_SECRET_KEY', 'test-email-secret')
    monkeypatch.setattr(Env, 'EMAIL_VERIFICATION_SALT', 'test-email-salt')
    monkeypatch.setattr(Env, 'EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS', 3600)
    monkeypatch.setattr(
        ItsdangerousEmailVerificationProvider,
        '_invalidated_tokens',
        cast('Any', invalidated_tokens),
    )

    yield

    monkeypatch.setattr(
        ItsdangerousEmailVerificationProvider,
        '_invalidated_tokens',
        cast('Any', invalidated_tokens),
    )


@pytest.fixture
def create_account(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> CreateAccountFixture:
    def _create_account(
        *,
        name: str = 'Maria Silva',
        email: str = 'maria@example.com',
        password_hash: str | None = None,
        is_verified: bool = False,
        is_active: bool = True,
    ) -> AccountModel:
        session = sqlalchemy_session_factory()
        model = AccountModel(
            id=str(ULID()),
            name=name,
            email=email,
            password_hash=password_hash or 'stored-hash',
            is_verified=is_verified,
            is_active=is_active,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        session.expunge(model)
        session.close()
        return model

    return _create_account
