from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    PetitionDraftModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_case_assessment_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    with_petition_draft: bool,
) -> str:
    analysis_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise com minuta de petição',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_case_assessment().dto,
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
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
    session.commit()
    session.close()

    return analysis_id


class TestGetPetitionDraftController:
    def test_should_return_200_and_petition_draft_when_draft_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_petition_draft=True,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'analysis_id': analysis_id,
            'structured_facts': 'Fatos estruturados',
            'legal_grounds': 'Fundamentos jurídicos',
            'central_thesis': 'Tese central',
            'requests': ['Pedido 1'],
            'precedent_citations': ['STJ REsp 123 - tese aplicável'],
        }

    def test_should_return_404_when_draft_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_petition_draft=False,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Minuta da petição indisponivel',
        }

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
        requester_account = create_account(
            email='requester@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=owner_account.id,
            with_petition_draft=True,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(requester_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Esta analise nao pertence a sua conta.',
        }
