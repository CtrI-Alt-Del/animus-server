from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake import CaseAssessmentBriefingModel
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_analyses_repository import (
    SqlalchemyAnalysesRepository,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient
from tests.rest.controllers.intake.conftest import (
    BuildAuthHeadersFixture,
    CreateAnalysisFixture,
)


def _persist_case_assessment_briefing(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
) -> None:
    session = sqlalchemy_session_factory()
    session.add(
        CaseAssessmentBriefingModel(
            analysis_id=analysis_id,
            legal_area='CIVIL',
            court_jurisdiction='TJSP',
            main_claims='Pedido principal',
            intended_thesis='Tese principal',
            created_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
            updated_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
        )
    )
    session.commit()
    session.close()


class TestTriggerCaseAssessmentCaseSummarizationController:
    def test_should_return_202_publish_event_and_update_analysis_status(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_briefing_submitted().dto,
        )
        _persist_case_assessment_briefing(
            sqlalchemy_session_factory,
            analysis_id=analysis.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-summaries/case-assessment',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 202
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name
            == 'intake/case_assessment.case_summary.triggered'
        )
        assert fake_inngest_client.sent_events[0].data['analysis_id'] == analysis.id

        session = sqlalchemy_session_factory()
        persisted_analysis = SqlalchemyAnalysesRepository(session).find_by_id(
            Id.create(analysis.id)
        )
        session.close()

        assert persisted_analysis is not None
        assert (
            persisted_analysis.status.value
            == CaseAssessmentAnalysisStatus.create_as_analyzing_case().dto
        )

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        authenticated_account = create_account(is_verified=True, is_active=True)
        owner_account = create_account(
            email='owner@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(
            account_id=owner_account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_briefing_submitted().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-summaries/case-assessment',
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Análise nao pertence a conta autenticada',
        }
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_404_when_case_assessment_briefing_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-summaries/case-assessment',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Briefing da analise nao encontrado',
        }
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_400_when_analysis_type_is_not_case_assessment(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            status='DOCUMENT_UPLOADED',
        )
        _persist_case_assessment_briefing(
            sqlalchemy_session_factory,
            analysis_id=analysis.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-summaries/case-assessment',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 400
        assert response.json() == {
            'title': 'Erro de validação',
            'message': 'Tipo de análise incoerente',
        }
        assert len(fake_inngest_client.sent_events) == 0
