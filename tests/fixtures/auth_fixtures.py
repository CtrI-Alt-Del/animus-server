from collections.abc import Callable, Iterator
import pytest
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.constants import Env
from animus.database.sqlalchemy.models.auth import AccountModel

CreateAccountFixture = Callable[..., AccountModel]
_DEFAULT_PASSWORD_HASH = object()


@pytest.fixture(autouse=True)
def auth_test_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(Env, 'JWT_SECRET_KEY', 'test-jwt-secret')
    monkeypatch.setattr(Env, 'EMAIL_VERIFICATION_OTP_TTL_SECONDS', 3600)

    yield


@pytest.fixture
def create_account(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> CreateAccountFixture:
    def _create_account(
        *,
        name: str = 'Maria Silva',
        email: str = 'maria@example.com',
        password_hash: str | None | object = _DEFAULT_PASSWORD_HASH,
        is_verified: bool = False,
        is_active: bool = True,
    ) -> AccountModel:
        session = sqlalchemy_session_factory()
        model = AccountModel(
            id=str(ULID()),
            name=name,
            email=email,
            password_hash=(
                'stored-hash'
                if password_hash is _DEFAULT_PASSWORD_HASH
                else password_hash
            ),
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
