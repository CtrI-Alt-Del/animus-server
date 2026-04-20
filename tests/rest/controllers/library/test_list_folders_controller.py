from collections.abc import Callable

from fastapi.testclient import TestClient

from animus.database.sqlalchemy.models.intake import AnalysisModel
from animus.database.sqlalchemy.models.library import FolderModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]
CreateFolderFixture = Callable[..., FolderModel]


class TestListFoldersController:
    def test_should_return_only_active_folders_from_authenticated_account_with_counts(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_folder: CreateFolderFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        other_account = create_account(
            email='other@example.com',
            is_verified=True,
            is_active=True,
        )
        first_folder = create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
            name='Pasta A',
        )
        second_folder = create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS0',
            name='Pasta B',
        )
        create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS1',
            name='Arquivada',
            is_archived=True,
        )
        create_folder(
            account_id=other_account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS2',
            name='Outra conta',
        )

        create_analysis(account_id=account.id, folder_id=first_folder.id)
        create_analysis(account_id=account.id, folder_id=first_folder.id)
        create_analysis(
            account_id=account.id,
            folder_id=first_folder.id,
            is_archived=True,
        )
        create_analysis(account_id=account.id, folder_id=second_folder.id)

        response = client.get(
            '/library/folders?limit=10',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'items': [
                {
                    'id': first_folder.id,
                    'name': 'Pasta A',
                    'analysis_count': 2,
                    'account_id': account.id,
                    'is_archived': False,
                },
                {
                    'id': second_folder.id,
                    'name': 'Pasta B',
                    'analysis_count': 1,
                    'account_id': account.id,
                    'is_archived': False,
                },
            ],
            'next_cursor': None,
        }
