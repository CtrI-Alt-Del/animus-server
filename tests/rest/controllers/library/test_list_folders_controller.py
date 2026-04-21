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
        create_analysis(account_id=other_account.id, folder_id=first_folder.id)
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

    def test_should_return_next_cursor_and_the_next_page(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        first_folder = create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS3',
            name='Pasta 1',
        )
        second_folder = create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS4',
            name='Pasta 2',
        )
        third_folder = create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS5',
            name='Pasta 3',
        )

        first_response = client.get(
            '/library/folders',
            params={'limit': 2, 'search': 'Pasta'},
            headers=build_auth_headers(account.id),
        )
        second_response = client.get(
            '/library/folders',
            params={
                'limit': 2,
                'search': 'Pasta',
                'cursor': second_folder.id,
            },
            headers=build_auth_headers(account.id),
        )

        assert first_response.status_code == 200
        assert first_response.json() == {
            'items': [
                {
                    'id': first_folder.id,
                    'name': 'Pasta 1',
                    'analysis_count': 0,
                    'account_id': account.id,
                    'is_archived': False,
                },
                {
                    'id': second_folder.id,
                    'name': 'Pasta 2',
                    'analysis_count': 0,
                    'account_id': account.id,
                    'is_archived': False,
                },
            ],
            'next_cursor': second_folder.id,
        }
        assert second_response.status_code == 200
        assert second_response.json() == {
            'items': [
                {
                    'id': third_folder.id,
                    'name': 'Pasta 3',
                    'analysis_count': 0,
                    'account_id': account.id,
                    'is_archived': False,
                }
            ],
            'next_cursor': None,
        }

    def test_should_filter_folders_by_search_term(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_folder: CreateFolderFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        matching_folder = create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS6',
            name='Processos civeis',
        )
        create_folder(
            account_id=account.id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS7',
            name='Contratos',
        )

        response = client.get(
            '/library/folders',
            params={'limit': 10, 'search': 'civeis'},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'items': [
                {
                    'id': matching_folder.id,
                    'name': 'Processos civeis',
                    'analysis_count': 0,
                    'account_id': account.id,
                    'is_archived': False,
                }
            ],
            'next_cursor': None,
        }
