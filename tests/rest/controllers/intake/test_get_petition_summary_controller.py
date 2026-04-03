from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    PetitionModel,
    PetitionSummaryModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_petition_with_summary(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> str:
    analysis_id = str(ULID())
    petition_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise da peticao',
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
            uploaded_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
            document_file_path='petitions/initial-petition.pdf',
            document_name='Peticao inicial.pdf',
        )
    )
    session.add(
        PetitionSummaryModel(
            petition_id=petition_id,
            case_summary='Resumo objetivo da peticao inicial',
            legal_issue='Controversia sobre inadimplemento contratual',
            central_question='Ha inadimplemento apto a justificar condenacao?',
            relevant_laws=['Codigo Civil, Art. 389'],
            key_facts=['Contrato firmado e nao adimplido'],
            search_terms=['inadimplemento contratual'],
        )
    )
    session.commit()
    session.close()

    return petition_id


class TestGetPetitionSummaryController:
    def test_should_return_200_and_petition_summary_when_petition_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        petition_id = _create_petition_with_summary(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.get(
            f'/intake/petitions/{petition_id}/summary',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'case_summary': 'Resumo objetivo da peticao inicial',
            'legal_issue': 'Controversia sobre inadimplemento contratual',
            'central_question': 'Ha inadimplemento apto a justificar condenacao?',
            'relevant_laws': ['Codigo Civil, Art. 389'],
            'key_facts': ['Contrato firmado e nao adimplido'],
            'search_terms': ['inadimplemento contratual'],
        }

    def test_should_return_403_when_petition_belongs_to_another_account(
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
        petition_id = _create_petition_with_summary(
            sqlalchemy_session_factory,
            account_id=owner_account.id,
        )

        response = client.get(
            f'/intake/petitions/{petition_id}/summary',
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Peticao nao pertence a conta autenticada',
        }

    def test_should_return_422_when_petition_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/petitions/invalid-petition-id/summary',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
