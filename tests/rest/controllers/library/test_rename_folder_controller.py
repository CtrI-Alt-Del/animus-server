from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.library import FolderModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateFolderFixture = Callable[..., FolderModel]


class TestRenameFolderController:
    def test_should_return_200_and_persist_new_name(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        folder = create_folder(account_id=account.id, name='Nome antigo')

        response = client.patch(
            f'/library/folders/{folder.id}',
            json={'name': 'Nome novo'},
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_folder = inspection_session.scalar(
            select(FolderModel).where(FolderModel.id == folder.id)
        )
        inspection_session.close()

        assert response.status_code == 200
        assert persisted_folder is not None
        assert persisted_folder.name == 'Nome novo'
        assert response.json() == {
            'id': folder.id,
            'name': 'Nome novo',
            'analysis_count': 0,
            'account_id': account.id,
            'is_archived': False,
        }
