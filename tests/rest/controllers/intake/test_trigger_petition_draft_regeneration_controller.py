from datetime import UTC, datetime

import pytest
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
    PetitionDraftModel,
    PrecedentModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_case_assessment_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    with_petition_draft: bool,
    chosen_flags: list[bool],
) -> str:
    analysis_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise com minuta para regeração',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_done().dto,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
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

    if with_petition_draft:
        session.add(
            PetitionDraftModel(
                analysis_id=analysis_id,
                structured_facts='Fatos estruturados',
                legal_grounds='Fundamentos jurídicos',
                central_thesis='Tese central',
                requests=['Pedido 1'],
                precedent_citations=['STJ REsp 123 - tese aplicável'],
            )
        )

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

    return analysis_id


class TestTriggerPetitionDraftRegenerationController:
    def test_should_return_202_when_preconditions_are_satisfied(
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
            with_petition_draft=True,
            chosen_flags=[True, False],
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts/regenerate',
            headers=build_auth_headers(account.id),
            json={'comments': '  Ajuste os pedidos finais.  '},
        )

        assert response.status_code == 202
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name
            == 'intake/petition_draft.regeneration.triggered'
        )
        assert fake_inngest_client.sent_events[0].data == {
            'analysis_id': analysis_id,
            'comments': 'Ajuste os pedidos finais.',
        }

    @pytest.mark.parametrize('payload', [{}, {'comments': '   '}])
    def test_should_return_422_when_comments_are_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        payload: dict[str, str],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_petition_draft=True,
            chosen_flags=[True],
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts/regenerate',
            headers=build_auth_headers(account.id),
            json=payload,
        )

        assert response.status_code == 422

    def test_should_return_422_when_petition_draft_is_unavailable(
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
            with_petition_draft=False,
            chosen_flags=[True],
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/petition-drafts/regenerate',
            headers=build_auth_headers(account.id),
            json={'comments': 'Revise a minuta atual'},
        )

        assert response.status_code == 422
        assert response.json() == {
            'title': 'Pre-condição de regeração de minuta invalida',
            'message': 'Nao ha minuta de petição persistida para regeração',
        }
        assert len(fake_inngest_client.sent_events) == 0
