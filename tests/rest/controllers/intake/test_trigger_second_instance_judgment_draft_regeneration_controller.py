from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    CaseSummaryModel,
    PrecedentModel,
    SecondInstanceDecisionModel,
    SecondInstanceJudgmentDraftModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_second_instance_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> str:
    analysis_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise de segunda instancia',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_case_analyzed().dto,
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
            case_summary='Resumo',
            legal_issue='Questão',
            central_question='Pergunta',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['Termo 1'],
        )
    )
    session.commit()
    session.close()


def _persist_chosen_precedent(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
) -> None:
    precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STJ',
            kind='RG',
            number=123,
            status='vigente',
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
            similarity_score=98.0,
            synthesis='Síntese',
        )
    )
    session.commit()
    session.close()


def _persist_second_instance_decision(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
) -> None:
    session = sqlalchemy_session_factory()
    session.add(
        SecondInstanceDecisionModel(
            analysis_id=analysis_id,
            description='Dar parcial provimento ao recurso.',
        )
    )
    session.commit()
    session.close()


def _persist_judgment_draft(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
) -> None:
    session = sqlalchemy_session_factory()
    session.add(
        SecondInstanceJudgmentDraftModel(
            analysis_id=analysis_id,
            report='Relatório',
            merit_analysis='Fundamentação',
            precedent_adherence_analysis='Aderência',
            ruling=['Item 1'],
            preliminary_issues='Preliminar',
            no_applicable_precedent_notice='Aviso',
        )
    )
    session.commit()
    session.close()


class TestTriggerSecondInstanceJudgmentDraftRegenerationController:
    def test_should_return_202_when_request_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )
        _persist_case_summary(sqlalchemy_session_factory, analysis_id=analysis_id)
        _persist_chosen_precedent(sqlalchemy_session_factory, analysis_id=analysis_id)
        _persist_second_instance_decision(
            sqlalchemy_session_factory,
            analysis_id=analysis_id,
        )
        _persist_judgment_draft(sqlalchemy_session_factory, analysis_id=analysis_id)

        response = client.post(
            f'/intake/analyses/{analysis_id}/judgment-drafts/regenerate',
            json={'comments': '  Ajustar fundamentação e dispositivo.  '},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 202
        assert response.content == b''
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name
            == 'intake/judgment_draft.regeneration.triggered'
        )
        assert fake_inngest_client.sent_events[0].data == {
            'analysis_id': analysis_id,
            'comments': 'Ajustar fundamentação e dispositivo.',
        }

    @pytest.mark.parametrize('payload', [{}, {'comments': ''}, {'comments': '   '}])
    def test_should_return_422_when_body_is_invalid(
        self,
        payload: dict[str, str],
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/judgment-drafts/regenerate',
            json=payload,
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_422_when_judgment_draft_is_unavailable_for_regeneration(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
        )
        _persist_case_summary(sqlalchemy_session_factory, analysis_id=analysis_id)
        _persist_chosen_precedent(sqlalchemy_session_factory, analysis_id=analysis_id)
        _persist_second_instance_decision(
            sqlalchemy_session_factory,
            analysis_id=analysis_id,
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/judgment-drafts/regenerate',
            json={'comments': 'Revisar minuta'},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
        assert response.json() == {
            'title': 'Pre-condicao de regeracao de minuta invalida',
            'message': 'Nao ha minuta de sentenca persistida para regeracao',
        }
        assert len(fake_inngest_client.sent_events) == 0
