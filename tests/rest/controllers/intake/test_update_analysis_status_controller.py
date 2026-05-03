from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.intake import AnalysisModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


class TestUpdateAnalysisStatusController:
    def test_should_return_200_and_update_analysis_status(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.patch(
            f'/intake/analyses/{analysis.id}/status',
            json={'status': 'failed'},
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_analysis = inspection_session.scalar(
            select(AnalysisModel).where(AnalysisModel.id == analysis.id)
        )
        inspection_session.close()

        assert response.status_code == 200
        assert persisted_analysis is not None
        assert persisted_analysis.status == 'FAILED'
        assert response.json() == {'value': 'FAILED'}

    def test_should_return_403_when_analysis_belongs_to_another_account(
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
        owner_account = create_account(
            email='bruna@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(account_id=owner_account.id)

        response = client.patch(
            f'/intake/analyses/{analysis.id}/status',
            json={'status': 'FAILED'},
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Analise nao pertence a conta autenticada',
        }

    def test_should_return_400_when_status_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.patch(
            f'/intake/analyses/{analysis.id}/status',
            json={'status': 'invalid_status'},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 400
        assert response.json() == {
            'title': 'Erro de validação',
            'message': 'Status de analise invalido: invalid_status',
        }
