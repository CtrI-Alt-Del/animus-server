from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    PrecedentModel,
)
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


def _build_auth_headers(account_id: str) -> dict[str, str]:
    access_token = JoseJwtProvider().encode(Text.create(account_id)).access_token.value
    return {'Authorization': f'Bearer {access_token}'}


def _create_analysis_and_precedent(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> tuple[str, str]:
    analysis_id = str(ULID())
    precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise de precedentes',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_first_instance().dto,
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STF',
            kind='RG',
            number=101,
            status='vigente',
            enunciation='Enunciado do precedente',
            thesis='Tese do precedente',
            last_updated_in_pangea_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.close()

    return analysis_id, precedent_id


class TestCreateAnalysisPrecedentController:
    def test_should_return_201_and_persist_analysis_precedent(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id, precedent_id = _create_analysis_and_precedent(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/precedents',
            json={
                'court': 'STF',
                'kind': 'RG',
                'number': 101,
            },
            headers=_build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_analysis_precedent = inspection_session.scalar(
            select(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis_id,
                AnalysisPrecedentModel.precedent_id == precedent_id,
            )
        )
        inspection_session.close()

        assert response.status_code == 201
        assert persisted_analysis_precedent is not None
        assert response.json()['analysis_id'] == analysis_id
        assert response.json()['precedent']['identifier'] == {
            'court': 'STF',
            'kind': 'RG',
            'number': 101,
        }

    def test_should_return_404_when_precedent_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id, _ = _create_analysis_and_precedent(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis_id}/precedents',
            json={
                'court': 'STF',
                'kind': 'RG',
                'number': 999,
            },
            headers=_build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Precedente nao encontrado',
        }
