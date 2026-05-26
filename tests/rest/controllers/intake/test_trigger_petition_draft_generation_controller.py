from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    CaseSummaryModel,
    PrecedentModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_case_assessment_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    analysis_type: str = AnalysisType.create_as_case_assessment().dto,
) -> str:
    analysis_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise de caso',
            folder_id=None,
            account_id=account_id,
            type=analysis_type,
            status=CaseAssessmentAnalysisStatus.create_as_precedents_searched().dto,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.close()

    return analysis_id


def _persist_case_summary(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
) -> None:
    session = sqlalchemy_session_factory()
    session.add(
        CaseSummaryModel(
            analysis_id=analysis_id,
            case_summary='Resumo do caso',
            legal_issue='Questão jurídica',
            central_question='Pergunta central',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['Termo 1'],
        )
    )
    session.commit()
    session.close()


def _persist_analysis_precedents(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
    chosen_flags: list[bool],
) -> None:
    session = sqlalchemy_session_factory()

    for index, is_chosen in enumerate(chosen_flags, start=1):
        precedent_id = str(ULID())
        session.add(
            PrecedentModel(
                id=precedent_id,
                court='STF',
                kind='RG',
                number=index,
                status='vigente',
                enunciation=f'Enunciado {index}',
                thesis=f'Tese {index}',
                last_updated_in_pangea_at=datetime.now(UTC),
            )
        )
        session.add(
            AnalysisPrecedentModel(
                analysis_id=analysis_id,
                precedent_id=precedent_id,
                is_chosen=is_chosen,
                similarity_score=95.0 - index,
                synthesis=f'Síntese {index}',
            )
        )

    session.commit()
    session.close()


class TestTriggerPetitionDraftGenerationController:
    def test_should_return_202_when_there_is_at_least_one_chosen_precedent(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )
        _persist_case_summary(sqlalchemy_session_factory, analysis_id=analysis_id)
        _persist_analysis_precedents(
            sqlalchemy_session_factory,
            analysis_id=analysis_id,
            chosen_flags=[True, False],
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 202
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name
            == 'intake/petition_draft.generation.triggered'
        )
        assert fake_inngest_client.sent_events[0].data['analysis_id'] == analysis_id

    def test_should_return_400_when_analysis_type_is_not_case_assessment(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            analysis_type=AnalysisType.create_as_first_instance().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 400
        assert response.json() == {
            'title': 'Erro de validação',
            'message': 'Tipo de análise incoerente',
        }
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_404_when_case_summary_is_unavailable(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Resumo do caso indisponivel',
        }
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_404_when_analysis_has_no_precedents(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )
        _persist_case_summary(sqlalchemy_session_factory, analysis_id=analysis_id)

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Precedentes da analise indisponiveis',
        }
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_409_when_no_precedent_is_chosen(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )
        _persist_case_summary(sqlalchemy_session_factory, analysis_id=analysis_id)
        _persist_analysis_precedents(
            sqlalchemy_session_factory,
            analysis_id=analysis_id,
            chosen_flags=[False, False],
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 409
        assert response.json() == {
            'title': 'Erro de conflito',
            'message': 'Pelo menos um precedente escolhido e obrigatorio',
        }
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        owner_account = create_account(
            is_verified=True,
            is_active=True,
            email='owner@example.com',
        )
        requester_account = create_account(
            is_verified=True,
            is_active=True,
            email='requester@example.com',
        )
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=owner_account.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(requester_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Análise nao pertence a conta autenticada',
        }
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_422_when_analysis_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.post(
            '/intake/analyses/invalid-analysis-id/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
