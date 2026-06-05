from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.database.sqlalchemy.models.intake import (
    AnalysisDocumentModel,
    AnalysisModel,
    AnalysisPrecedentModel,
    CaseSummaryModel,
    PrecedentModel,
    SecondInstanceDecisionModel,
    SecondInstanceJudgmentDraftModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_second_instance_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    with_judgment_draft: bool,
) -> str:
    analysis_id = str(ULID())
    precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise de segunda instância',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_second_instance().dto,
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        AnalysisDocumentModel(
            analysis_id=analysis_id,
            uploaded_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
            document_file_path='analyses/document.pdf',
            document_name='document.pdf',
        )
    )
    session.add(
        CaseSummaryModel(
            analysis_id=analysis_id,
            case_summary='Resumo original',
            legal_issue='Questão original',
            central_question='Pergunta original',
            relevant_laws=['Lei original'],
            key_facts=['Fato original'],
            search_terms=['Termo original'],
        )
    )
    session.add(
        SecondInstanceDecisionModel(
            analysis_id=analysis_id,
            description='Dar parcial provimento ao recurso.',
        )
    )
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STJ',
            kind='SV',
            number=123,
            status='Vigente',
            enunciation='Enunciado original',
            thesis='Tese original',
            last_updated_in_pangea_at=datetime.now(UTC),
        )
    )
    session.add(
        AnalysisPrecedentModel(
            analysis_id=analysis_id,
            precedent_id=precedent_id,
            is_chosen=True,
            similarity_score=91.0,
            synthesis='Síntese original',
        )
    )
    if with_judgment_draft:
        session.add(
            SecondInstanceJudgmentDraftModel(
                analysis_id=analysis_id,
                report='Relatório original',
                merit_analysis='Mérito original',
                precedent_adherence_analysis='Aderência original',
                ruling=['Dispositivo original'],
                preliminary_issues='Preliminar original',
                no_applicable_precedent_notice='Aviso original',
            )
        )
    session.commit()
    session.close()

    return analysis_id


def _build_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        'report': '  Relatório atualizado com espaços  ',
        'merit_analysis': '  Mérito atualizado com espaços  ',
        'precedent_adherence_analysis': '  Aderência atualizada com espaços  ',
        'ruling': ['  Dispositivo 1  ', 'Dispositivo 2'],
        'preliminary_issues': None,
        'no_applicable_precedent_notice': None,
    }
    payload.update(overrides)
    return payload


class TestUpdateSecondInstanceJudgmentDraftController:
    def test_should_return_200_and_persist_updated_draft_and_reflect_it_on_get_and_report(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_judgment_draft=True,
        )
        payload = _build_payload()
        expected_payload = {
            'analysis_id': analysis_id,
            'report': 'Relatório atualizado com espaços',
            'merit_analysis': 'Mérito atualizado com espaços',
            'precedent_adherence_analysis': 'Aderência atualizada com espaços',
            'ruling': ['Dispositivo 1', 'Dispositivo 2'],
            'preliminary_issues': None,
            'no_applicable_precedent_notice': None,
        }

        response = client.put(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
            json=payload,
        )

        assert response.status_code == 200
        assert response.json() == expected_payload

        session = sqlalchemy_session_factory()
        judgment_draft = session.get(SecondInstanceJudgmentDraftModel, analysis_id)

        assert judgment_draft is not None
        assert judgment_draft.report == expected_payload['report']
        assert judgment_draft.merit_analysis == expected_payload['merit_analysis']
        assert (
            judgment_draft.precedent_adherence_analysis
            == expected_payload['precedent_adherence_analysis']
        )
        assert judgment_draft.ruling == expected_payload['ruling']
        assert judgment_draft.preliminary_issues is None
        assert judgment_draft.no_applicable_precedent_notice is None

        session.close()

        get_response = client.get(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
        )

        assert get_response.status_code == 200
        assert get_response.json() == expected_payload

        report_response = client.get(
            f'/intake/analyses/{analysis_id}/second-instance-report',
            headers=build_auth_headers(account.id),
        )

        assert report_response.status_code == 200
        assert report_response.json()['draft'] == expected_payload

    def test_should_return_404_when_judgment_draft_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_judgment_draft=False,
        )

        response = client.put(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
            json=_build_payload(),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Minuta do julgamento indisponivel',
        }

    @pytest.mark.parametrize(
        ('payload', 'field_name'),
        [
            pytest.param(
                _build_payload(report='   '),
                'report',
                id='blank-report',
            ),
            pytest.param(
                _build_payload(merit_analysis='   '),
                'merit_analysis',
                id='blank-merit-analysis',
            ),
            pytest.param(
                _build_payload(precedent_adherence_analysis='   '),
                'precedent_adherence_analysis',
                id='blank-precedent-adherence-analysis',
            ),
            pytest.param(
                _build_payload(ruling=[]),
                'ruling',
                id='empty-ruling',
            ),
            pytest.param(
                _build_payload(ruling=['Dispositivo válido', '   ']),
                'ruling',
                id='blank-ruling-item',
            ),
        ],
    )
    def test_should_return_422_when_payload_contains_blank_or_empty_values(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        payload: dict[str, object],
        field_name: str,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_judgment_draft=True,
        )

        response = client.put(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
            json=payload,
        )

        assert response.status_code == 422
        assert any(
            error['loc'] == ['body', field_name] for error in response.json()['detail']
        )

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        owner_account = create_account(
            email='owner-update-second-instance-draft@example.com',
            is_verified=True,
            is_active=True,
        )
        requester_account = create_account(
            email='requester-update-second-instance-draft@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis_id = _create_second_instance_analysis(
            sqlalchemy_session_factory,
            account_id=owner_account.id,
            with_judgment_draft=True,
        )

        response = client.put(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(requester_account.id),
            json=_build_payload(),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Análise nao pertence a conta autenticada',
        }
