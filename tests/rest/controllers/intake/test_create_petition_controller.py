from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.models.intake import AnalysisModel, PetitionModel
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture

CreateAnalysisFixture = Callable[..., AnalysisModel]


def _build_auth_headers(account_id: str) -> dict[str, str]:
    access_token = JoseJwtProvider().encode(Text.create(account_id)).access_token.value
    return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def create_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> CreateAnalysisFixture:
    def _create_analysis(
        *,
        account_id: str,
        analysis_id: str | None = None,
        name: str = 'Analise inicial',
        status: str = AnalysisStatusValue.WAITING_PETITION.value,
        folder_id: str | None = None,
        is_archived: bool = False,
    ) -> AnalysisModel:
        session = sqlalchemy_session_factory()
        model = AnalysisModel(
            id=analysis_id or str(ULID()),
            name=name,
            folder_id=folder_id,
            account_id=account_id,
            status=status,
            is_archived=is_archived,
            created_at=datetime.now(UTC),
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        session.expunge(model)
        session.close()
        return model

    return _create_analysis


class TestCreatePetitionController:
    def test_should_return_201_and_persist_petition_when_payload_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)
        payload = {
            'analysis_id': analysis.id,
            'uploaded_at': '2026-03-27T10:30:00+00:00',
            'document': {
                'file_path': 'petitions/initial-petition.pdf',
                'name': 'Peticao inicial.pdf',
            },
        }

        response = client.post(
            '/intake/petitions',
            json=payload,
            headers=_build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_petition = inspection_session.scalar(
            select(PetitionModel).where(PetitionModel.analysis_id == analysis.id)
        )
        inspection_session.close()

        assert response.status_code == 201
        assert persisted_petition is not None
        assert response.json() == {
            'id': persisted_petition.id,
            'analysis_id': analysis.id,
            'uploaded_at': '2026-03-27T10:30:00+00:00',
            'document': {
                'file_path': 'petitions/initial-petition.pdf',
                'name': 'Peticao inicial.pdf',
            },
        }
        assert persisted_petition.document_file_path == 'petitions/initial-petition.pdf'
        assert persisted_petition.document_name == 'Peticao inicial.pdf'

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        authenticated_account = create_account(
            email='ana@example.com',
            is_verified=True,
            is_active=True,
        )
        owner_account = create_account(
            email='bruna@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(account_id=owner_account.id)

        response = client.post(
            '/intake/petitions',
            json={
                'analysis_id': analysis.id,
                'uploaded_at': '2026-03-27T10:30:00+00:00',
                'document': {
                    'file_path': 'petitions/foreign-petition.pdf',
                    'name': 'Peticao de terceiro.pdf',
                },
            },
            headers=_build_auth_headers(authenticated_account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_petitions = inspection_session.scalars(select(PetitionModel)).all()
        inspection_session.close()

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Analise nao pertence a conta autenticada',
        }
        assert persisted_petitions == []

    def test_should_return_422_when_document_name_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.post(
            '/intake/petitions',
            json={
                'analysis_id': analysis.id,
                'uploaded_at': '2026-03-27T10:30:00+00:00',
                'document': {
                    'file_path': 'petitions/initial-petition.pdf',
                },
            },
            headers=_build_auth_headers(account.id),
        )

        assert response.status_code == 422
