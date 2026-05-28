from datetime import UTC, datetime
from typing import Callable

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    PrecedentModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


def _create_precedent(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    number: int = 101,
) -> str:
    precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STF',
            kind='RG',
            number=number,
            status='vigente',
            enunciation=f'Enunciado do precedente {number}',
            thesis=f'Tese do precedente {number}',
            last_updated_in_pangea_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.close()

    return precedent_id


class TestAddAnalysisPrecedentByIdentifierController:
    def test_should_return_200_and_add_new_precedent_to_analysis(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            status='DONE',
        )
        precedent_id = _create_precedent(sqlalchemy_session_factory, number=101)

        response = client.post(
            f'/intake/analyses/{analysis.id}/precedents',
            json={
                'court': 'STF',
                'kind': 'RG',
                'number': 101,
            },
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        relation = inspection_session.scalar(
            select(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis.id,
                AnalysisPrecedentModel.precedent_id == precedent_id,
            )
        )
        inspection_session.close()

        assert response.status_code == 200
        assert response.json() == {'value': 'DONE'}
        assert relation is not None
        assert relation.is_chosen is True
        assert relation.applicability_level == 2
        assert relation.is_manually_added is True

    def test_should_return_200_and_choose_existing_precedent_when_already_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            status='DONE',
        )
        precedent_id = _create_precedent(sqlalchemy_session_factory, number=101)

        # Pre-create unchosen relation
        session = sqlalchemy_session_factory()
        session.add(
            AnalysisPrecedentModel(
                analysis_id=analysis.id,
                precedent_id=precedent_id,
                is_chosen=False,
                similarity_score=80.0,
                synthesis='Sintese previa',
            )
        )
        session.commit()
        session.close()

        response = client.post(
            f'/intake/analyses/{analysis.id}/precedents',
            json={
                'court': 'STF',
                'kind': 'RG',
                'number': 101,
            },
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        relation = inspection_session.scalar(
            select(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis.id,
                AnalysisPrecedentModel.precedent_id == precedent_id,
            )
        )
        inspection_session.close()

        assert response.status_code == 200
        assert relation is not None
        assert relation.is_chosen is True

    def test_should_return_404_when_precedent_does_not_exist_in_pangea(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            status='DONE',
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/precedents',
            json={
                'court': 'STF',
                'kind': 'RG',
                'number': 999,  # Non-existent
            },
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Precedente nao encontrado',
        }

    def test_should_return_403_when_analysis_does_not_belong_to_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        authenticated_account = create_account(
            email='authenticated@example.com',
            is_verified=True,
            is_active=True,
        )
        owner_account = create_account(
            email='owner@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(
            account_id=owner_account.id,
            status='DONE',
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/precedents',
            json={
                'court': 'STF',
                'kind': 'RG',
                'number': 101,
            },
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Análise nao pertence a conta autenticada',
        }
