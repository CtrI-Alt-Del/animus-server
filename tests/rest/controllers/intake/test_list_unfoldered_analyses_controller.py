from collections.abc import Callable
from datetime import UTC

from fastapi.testclient import TestClient

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.database.sqlalchemy.models.intake import AnalysisModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


class TestListUnfolderedAnalysesController:
    def test_should_return_unfoldered_analyses_for_authenticated_account(
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

        first_analysis = create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5F0A',
            name='Analise sem pasta alfa',
        )

        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5F0B',
            name='Analise com pasta',
            folder_id='01ARZ3NDEKTSV4RRFFQ69G5F1A',
        )

        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5F0C',
            name='Analise sem pasta beta',
        )

        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5F0D',
            name='Analise arquivada',
            is_archived=True,
        )

        create_analysis(
            account_id=other_account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5F0E',
            name='Analise de outra conta',
        )

        response = client.get(
            '/intake/analyses/unfoldered',
            params={'limit': 1, 'search': 'Analise', 'is_archived': False},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'items': [
                {
                    'id': first_analysis.id,
                    'name': 'Analise sem pasta alfa',
                    'folder_id': None,
                    'account_id': account.id,
                    'status': AnalysisStatusValue.WAITING_PETITION.value,
                    'is_archived': False,
                    'precedents_search_filters': None,
                    'created_at': first_analysis.created_at.replace(
                        tzinfo=UTC
                    ).isoformat(),
                }
            ],
            'next_cursor': first_analysis.id,
        }

    def test_should_return_422_when_limit_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses/unfoldered',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422