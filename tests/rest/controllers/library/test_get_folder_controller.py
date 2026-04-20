from collections.abc import Callable

from fastapi.testclient import TestClient

from animus.database.sqlalchemy.models.library import FolderModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateFolderFixture = Callable[..., FolderModel]


class TestGetFolderController:
    def test_should_return_200_when_folder_belongs_to_authenticated_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        folder = create_folder(account_id=account.id, name='Pasta privada')

        response = client.get(
            f'/library/folders/{folder.id}',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'id': folder.id,
            'name': 'Pasta privada',
            'analysis_count': 0,
            'account_id': account.id,
            'is_archived': False,
        }

    def test_should_return_403_when_folder_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        owner = create_account(
            email='owner@example.com',
            is_verified=True,
            is_active=True,
        )
        viewer = create_account(
            email='viewer@example.com',
            is_verified=True,
            is_active=True,
        )
        folder = create_folder(account_id=owner.id)

        response = client.get(
            f'/library/folders/{folder.id}',
            headers=build_auth_headers(viewer.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Pasta nao pertence a conta autenticada',
        }
