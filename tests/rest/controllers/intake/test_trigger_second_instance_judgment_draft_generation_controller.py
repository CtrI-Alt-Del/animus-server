from datetime import UTC, datetime

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
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_second_instance_analysis_with_summary_and_precedents(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    chosen_flags: list[bool],
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
                similarity_score=90.0 - index,
                synthesis=f'Sintese {index}',
            )
        )

    session.commit()
    session.close()
    return analysis_id


class TestTriggerSecondInstanceJudgmentDraftGenerationController:
    def test_should_return_202_when_there_is_at_least_one_chosen_precedent(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis_with_summary_and_precedents(
            sqlalchemy_session_factory,
            account_id=account.id,
            chosen_flags=[True, False],
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 202
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name
            == 'intake/judgment_draft.generation.triggered'
        )
        assert fake_inngest_client.sent_events[0].data['analysis_id'] == analysis_id

    def test_should_return_409_when_no_precedent_is_chosen(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis_with_summary_and_precedents(
            sqlalchemy_session_factory,
            account_id=account.id,
            chosen_flags=[False, False],
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 409
        assert response.json() == {
            'title': 'Erro de conflito',
            'message': 'Pelo menos um precedente escolhido e obrigatorio',
        }
        assert len(fake_inngest_client.sent_events) == 0
