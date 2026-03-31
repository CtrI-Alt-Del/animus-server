from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
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


def _create_analysis_with_precedent(
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
            name='Analise de precedentes',
            folder_id=None,
            account_id=account_id,
            status=AnalysisStatusValue.WAITING_PRECEDENT_CHOISE.value,
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
    session.add(
        AnalysisPrecedentModel(
            analysis_id=analysis_id,
            precedent_id=precedent_id,
            is_chosen=False,
            applicability_percentage=84.5,
            synthesis='Sintese do precedente',
        )
    )
    session.commit()
    session.close()

    return analysis_id, precedent_id


class TestChooseAnalysisPrecedentController:
    def test_should_return_200_and_choose_precedent_when_query_params_are_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id, precedent_id = _create_analysis_with_precedent(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.patch(
            f'/intake/analyses/{analysis_id}/precedents/choose',
            params={
                'court': 'STF',
                'kind': 'RG',
                'number': 101,
            },
            headers=_build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_analysis = inspection_session.get(AnalysisModel, analysis_id)
        persisted_analysis_precedent = inspection_session.scalar(
            select(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis_id,
                AnalysisPrecedentModel.precedent_id == precedent_id,
            )
        )
        inspection_session.close()

        assert response.status_code == 200
        assert response.json() == {
            'value': AnalysisStatusValue.PRECEDENT_CHOSED.value,
        }
        assert persisted_analysis is not None
        assert persisted_analysis.status == AnalysisStatusValue.PRECEDENT_CHOSED.value
        assert persisted_analysis_precedent is not None
        assert persisted_analysis_precedent.is_chosen is True

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
