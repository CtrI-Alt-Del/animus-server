from collections.abc import Callable
from datetime import UTC

from fastapi.testclient import TestClient

from animus.database.sqlalchemy.models.intake import AnalysisModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


class TestListAnalysesController:
    def test_should_return_paginated_analyses_filtered_by_account_and_archive_state(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        other_account = create_account(
            email='other-account@example.com',
            is_verified=True,
            is_active=True,
        )
        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            name='Analise alfa',
        )
        second_analysis = create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAW',
            name='Analise beta',
        )
        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAX',
            name='Analise arquivada',
            is_archived=True,
        )
        create_analysis(
            account_id=other_account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAY',
            name='Analise de outra conta',
        )

        response = client.get(
            '/intake/analyses',
            params={'limit': 1, 'search': 'Analise', 'is_archived': False},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'items': [
                {
                    'id': second_analysis.id,
                    'name': second_analysis.name,
                    'folder_id': None,
                    'account_id': account.id,
                    'status': 'WAITING_PETITION',
                    'is_archived': False,
                    'precedents_search_filters': None,
                    'created_at': second_analysis.created_at.replace(
                        tzinfo=UTC
                    ).isoformat(),
                }
            ],
            'next_cursor': second_analysis.id,
        }

    def test_should_return_422_when_limit_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422

    def test_should_return_422_when_limit_is_zero(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses',
            params={'limit': 0},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
