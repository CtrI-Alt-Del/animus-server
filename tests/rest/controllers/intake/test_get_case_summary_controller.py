from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.database.sqlalchemy.models.intake import AnalysisModel, CaseSummaryModel
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_analysis_with_case_summary(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> str:
    analysis_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise',
            folder_id=None,
            account_id=account_id,
            type='FIRST_INSTANCE',
            status='CASE_ANALYZED',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        CaseSummaryModel(
            analysis_id=analysis_id,
            case_summary='Resumo do caso',
            legal_issue='Questao juridica',
            central_question='Pergunta central',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['termo 1'],
        )
    )
    session.commit()
    session.close()

    return analysis_id


class TestGetCaseSummaryController:
    def test_should_return_200_and_case_summary_when_summary_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_analysis_with_case_summary(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/case-summaries',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'case_summary': 'Resumo do caso',
            'legal_issue': 'Questao juridica',
            'central_question': 'Pergunta central',
            'relevant_laws': ['Lei 1'],
            'key_facts': ['Fato 1'],
            'search_terms': ['termo 1'],
            'type_of_action': None,
            'secondary_legal_issues': [],
            'alternative_questions': [],
            'jurisdiction_issue': None,
            'standing_issue': None,
            'requested_relief': [],
            'procedural_issues': [],
            'excluded_or_accessory_topics': [],
        }

    def test_should_return_422_when_analysis_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses/invalid-analysis-id/case-summaries',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
