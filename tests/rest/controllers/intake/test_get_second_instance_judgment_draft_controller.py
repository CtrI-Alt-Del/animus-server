from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    SecondInstanceJudgmentDraftModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_second_instance_analysis_with_draft(
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
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        SecondInstanceJudgmentDraftModel(
            analysis_id=analysis_id,
            report='Relatório',
            merit_analysis='Fundamentacao',
            precedent_adherence_analysis='Aderência',
            ruling=['Item 1', 'Item 2'],
            preliminary_issues='Preliminar',
            no_applicable_precedent_notice='Aviso',
        )
    )
    session.commit()
    session.close()

    return analysis_id


def _create_second_instance_analysis_without_draft(
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
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.close()

    return analysis_id


class TestGetSecondInstanceJudgmentDraftController:
    def test_should_return_200_and_judgment_draft_when_draft_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis_with_draft(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'analysis_id': analysis_id,
            'report': 'Relatório',
            'merit_analysis': 'Fundamentacao',
            'precedent_adherence_analysis': 'Aderência',
            'ruling': ['Item 1', 'Item 2'],
            'preliminary_issues': 'Preliminar',
            'no_applicable_precedent_notice': 'Aviso',
        }

    def test_should_return_404_when_draft_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_second_instance_analysis_without_draft(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/second-instance-judgment-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Minuta do julgamento indisponivel',
        }
