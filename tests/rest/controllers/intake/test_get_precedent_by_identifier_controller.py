from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.models.intake import (
    PrecedentModel,
)
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


def _build_auth_headers(account_id: str) -> dict[str, str]:
    access_token = JoseJwtProvider().encode(Text.create(account_id)).access_token.value
    return {'Authorization': f'Bearer {access_token}'}


def _create_precedent(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STF',
            kind='RG',
            number=101,
            status='vigente',
            enunciation='Enunciado do precedente',
            thesis='Tese do precedente',
            last_updated_in_pangea_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.close()


class TestGetPrecedentController:
    def test_should_return_200_and_precedent_when_identifier_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        _create_precedent(sqlalchemy_session_factory)

        response = client.get(
            '/intake/precedents',
            params={
                'court': 'STF',
                'kind': 'RG',
                'number': 101,
            },
            headers=_build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json()['identifier'] == {
            'court': 'STF',
            'kind': 'RG',
            'number': 101,
        }

    def test_should_return_404_when_precedent_identifier_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        _create_precedent(sqlalchemy_session_factory)

        response = client.get(
            '/intake/precedents',
            params={
                'court': 'STF',
                'kind': 'RG',
                'number': 999,
            },
            headers=_build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Precedente nao encontrado',
        }
