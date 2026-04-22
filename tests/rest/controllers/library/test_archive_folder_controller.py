from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.library import FolderModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateFolderFixture = Callable[..., FolderModel]


class TestArchiveFolderController:
    def test_should_return_200_and_archive_folder(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        folder = create_folder(account_id=account.id, is_archived=False)

        response = client.patch(
            f'/library/folders/{folder.id}/archive',
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_folder = inspection_session.scalar(
            select(FolderModel).where(FolderModel.id == folder.id)
        )
        inspection_session.close()

        assert response.status_code == 200
        assert persisted_folder is not None
        assert persisted_folder.is_archived is True
        assert response.json() == {
            'id': folder.id,
            'name': folder.name,
            'analysis_count': 0,
            'account_id': account.id,
            'is_archived': True,
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
        authenticated_account = create_account(
            email='viewer@example.com',
            is_verified=True,
            is_active=True,
        )
        folder = create_folder(account_id=owner.id)

        response = client.patch(
            f'/library/folders/{folder.id}/archive',
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Pasta nao pertence a conta autenticada',
        }

    def test_should_return_404_when_folder_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.patch(
            '/library/folders/01BX5ZZKBKACTAV9WEVGEMMVRZ/archive',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Pasta nao encontrada',
        }
