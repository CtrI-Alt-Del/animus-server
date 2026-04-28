from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.library import FolderModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]


class TestCreateFolderController:
    def test_should_return_201_and_persist_folder(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.post(
            '/library/folders',
            json={'name': 'Pasta de testes'},
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_folder = inspection_session.scalar(
            select(FolderModel).where(
                FolderModel.account_id == account.id,
                FolderModel.name == 'Pasta de testes',
            )
        )
        inspection_session.close()

        assert response.status_code == 201
        assert persisted_folder is not None
        assert response.json() == {
            'id': persisted_folder.id,
            'name': 'Pasta de testes',
            'analysis_count': 0,
            'account_id': account.id,
            'is_archived': False,
        }

    @pytest.mark.parametrize('name', ['A', 'a' * 51])
    def test_should_return_422_when_name_breaks_schema_constraints(
        self,
        name: str,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.post(
            '/library/folders',
            json={'name': name},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422

    def test_should_return_400_when_name_contains_only_spaces(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.post(
            '/library/folders',
            json={'name': '  '},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 400
        assert response.json()['title'] == 'Erro de validação'
        assert 'pelo menos 2 caracteres' in response.json()['message']
