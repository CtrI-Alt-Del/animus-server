from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    PetitionModel,
    PetitionSummaryModel,
    PrecedentModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_full_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    with_summary: bool = True,
) -> str:
    analysis_id = str(ULID())
    petition_id = str(ULID())
    precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise completa',
            folder_id=None,
            account_id=account_id,
            status=AnalysisStatusValue.PETITION_UPLOADED.value,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        PetitionModel(
            id=petition_id,
            analysis_id=analysis_id,
            uploaded_at=datetime.now(UTC),
            document_file_path='petitions/test.pdf',
            document_name='test.pdf',
        )
    )
    if with_summary:
        session.add(
            PetitionSummaryModel(
                petition_id=petition_id,
                case_summary='Resumo',
                legal_issue='Questao',
                central_question='Pergunta',
                relevant_laws=['Lei'],
                key_facts=['Fato'],
                search_terms=['Termo'],
            )
        )
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STF',
            kind='SV',
            number=123,
            status='Vigente',
            enunciation='Enunciado',
            thesis='Tese',
            last_updated_in_pangea_at=datetime.now(UTC),
        )
    )
    session.add(
        AnalysisPrecedentModel(
            analysis_id=analysis_id,
            precedent_id=precedent_id,
            is_chosen=True,
            similarity_percentage=90.0,
            synthesis='Sintese',
        )
    )
    session.commit()
    session.close()

    return analysis_id


class TestGetAnalysisReportController:
    def test_should_return_200_and_report_when_analysis_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_full_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/report',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        data = response.json()
        assert 'analysis' in data
        assert 'petition' in data
        assert 'summary' in data
        assert 'precedents' in data
        assert len(data['precedents']) == 1
        assert data['precedents'][0]['applicability_level'] == 0

    def test_should_return_404_when_analysis_not_found(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            f'/intake/analyses/{ULID()}/report',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        owner_account = create_account(
            email='owner@example.com',
            is_verified=True,
            is_active=True,
        )
        authenticated_account = create_account(
            email='authenticated@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis_id = _create_full_analysis(
            sqlalchemy_session_factory,
            account_id=owner_account.id,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/report',
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 403

    def test_should_return_404_when_summary_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_full_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_summary=False,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/report',
            headers=build_auth_headers(account.id),
        )

        # Let's see what it returns now
        assert response.status_code == 404
