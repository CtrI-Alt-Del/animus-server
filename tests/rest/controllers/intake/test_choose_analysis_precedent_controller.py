from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    PrecedentModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture


def _build_auth_headers(account_id: str) -> dict[str, str]:
    access_token = JoseJwtProvider().encode(Text.create(account_id)).access_token.value
    return {'Authorization': f'Bearer {access_token}'}


def _create_analysis_with_precedents(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> tuple[str, str, str]:
    analysis_id = str(ULID())
    first_precedent_id = str(ULID())
    second_precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise de precedentes',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_first_instance().dto,
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add_all(
        [
            PrecedentModel(
                id=first_precedent_id,
                court='STF',
                kind='RG',
                number=101,
                status='vigente',
                enunciation='Enunciado do precedente A',
                thesis='Tese do precedente A',
                last_updated_in_pangea_at=datetime.now(UTC),
            ),
            PrecedentModel(
                id=second_precedent_id,
                court='STF',
                kind='RG',
                number=202,
                status='vigente',
                enunciation='Enunciado do precedente B',
                thesis='Tese do precedente B',
                last_updated_in_pangea_at=datetime.now(UTC),
            ),
        ]
    )
    session.add_all(
        [
            AnalysisPrecedentModel(
                analysis_id=analysis_id,
                precedent_id=first_precedent_id,
                is_chosen=True,
                similarity_score=90.0,
                synthesis='Sintese A',
            ),
            AnalysisPrecedentModel(
                analysis_id=analysis_id,
                precedent_id=second_precedent_id,
                is_chosen=False,
                similarity_score=84.5,
                synthesis='Sintese B',
            ),
        ]
    )
    session.commit()
    session.close()

    return analysis_id, first_precedent_id, second_precedent_id


class TestChooseAnalysisPrecedentController:
    def test_should_return_200_and_choose_precedent_without_unchoosing_previous_one(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id, first_precedent_id, second_precedent_id = (
            _create_analysis_with_precedents(
                sqlalchemy_session_factory,
                account_id=account.id,
            )
        )

        response = client.patch(
            f'/intake/analyses/{analysis_id}/precedents/choose',
            params={
                'court': 'STF',
                'kind': 'RG',
                'number': 202,
            },
            headers=_build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        first_precedent = inspection_session.scalar(
            select(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis_id,
                AnalysisPrecedentModel.precedent_id == first_precedent_id,
            )
        )
        second_precedent = inspection_session.scalar(
            select(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis_id,
                AnalysisPrecedentModel.precedent_id == second_precedent_id,
            )
        )
        inspection_session.close()

        assert response.status_code == 200
        assert response.json() == {'value': 'DONE'}
        assert first_precedent is not None
        assert first_precedent.is_chosen is True
        assert second_precedent is not None
        assert second_precedent.is_chosen is True

    def test_should_return_422_when_number_query_param_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.patch(
            f'/intake/analyses/{ULID()!s}/precedents/choose',
            params={
                'court': 'STF',
                'kind': 'RG',
            },
            headers=_build_auth_headers(account.id),
        )

        assert response.status_code == 422
