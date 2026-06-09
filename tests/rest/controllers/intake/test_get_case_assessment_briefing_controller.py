from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    CaseAssessmentBriefingModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_case_assessment_analysis_with_briefing(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    with_briefing: bool,
) -> str:
    analysis_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise com briefing',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_case_assessment().dto,
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    if with_briefing:
        session.add(
            CaseAssessmentBriefingModel(
                analysis_id=analysis_id,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='Pedido principal da demanda',
                intended_thesis='Tese pretendida pela parte autora',
            )
        )
    session.commit()
    session.close()

    return analysis_id


class TestGetCaseAssessmentBriefingController:
    def test_should_return_200_and_briefing_when_briefing_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis_with_briefing(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_briefing=True,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/case-assessment-briefing',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'analysis_id': analysis_id,
            'legal_area': 'CIVIL',
            'court_jurisdiction': 'TJSP',
            'main_claims': 'Pedido principal da demanda',
            'intended_thesis': 'Tese pretendida pela parte autora',
        }

    def test_should_return_404_when_briefing_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis_with_briefing(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_briefing=False,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/case-assessment-briefing',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Briefing da analise nao encontrado',
        }

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        owner_account = create_account(
            email='owner-briefing@example.com',
            is_verified=True,
            is_active=True,
        )
        requester_account = create_account(
            email='requester-briefing@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis_id = _create_case_assessment_analysis_with_briefing(
            sqlalchemy_session_factory,
            account_id=owner_account.id,
            with_briefing=True,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/case-assessment-briefing',
            headers=build_auth_headers(requester_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Análise nao pertence a conta autenticada',
        }
