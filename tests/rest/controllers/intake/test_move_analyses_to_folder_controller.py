from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.intake import AnalysisModel
from animus.database.sqlalchemy.models.library import FolderModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]
CreateFolderFixture = Callable[..., FolderModel]


class TestMoveAnalysesToFolderController:
    def test_should_return_200_and_move_analyses_to_folder(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)
        folder = create_folder(account_id=account.id)

        response = client.patch(
            '/intake/analyses/folder',
            headers=build_auth_headers(account.id),
            json={'analysis_ids': [analysis.id], 'folder_id': folder.id},
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_analysis = inspection_session.scalar(
            select(AnalysisModel).where(AnalysisModel.id == analysis.id)
        )
        inspection_session.close()

        assert response.status_code == 200
        assert persisted_analysis is not None
        assert persisted_analysis.folder_id == folder.id
        assert response.json()[0]['folder_id'] == folder.id

    def test_should_return_404_when_folder_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        authenticated_account = create_account(
            email='ana@example.com',
            is_verified=True,
            is_active=True,
        )
        other_account = create_account(
            email='bruna@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(account_id=authenticated_account.id)
        folder = create_folder(account_id=other_account.id)

        response = client.patch(
            '/intake/analyses/folder',
            headers=build_auth_headers(authenticated_account.id),
            json={'analysis_ids': [analysis.id], 'folder_id': folder.id},
        )

        assert response.status_code == 404
        assert response.json()['message'] == 'Pasta nao encontrada'

    def test_should_return_404_when_any_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        authenticated_account = create_account(
            email='ana@example.com',
            is_verified=True,
            is_active=True,
        )
        other_account = create_account(
            email='bruna@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(account_id=other_account.id)

        response = client.patch(
            '/intake/analyses/folder',
            headers=build_auth_headers(authenticated_account.id),
            json={'analysis_ids': [analysis.id], 'folder_id': None},
        )

        assert response.status_code == 404
        assert response.json()['message'] == 'Analise nao encontrada'
