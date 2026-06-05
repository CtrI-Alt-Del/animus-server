from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.database.sqlalchemy.models.intake import (
    AnalysisPrecedentModel,
    PrecedentModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import (
    BuildAuthHeadersFixture,
    CreateAnalysisFixture,
)


def _create_precedent(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> PrecedentModel:
    session = sqlalchemy_session_factory()
    model = PrecedentModel(
        id=str(ULID()),
        court='STF',
        kind='RG',
        number=101,
        status='vigente',
        enunciation='Enunciado do precedente',
        thesis='Tese do precedente',
        last_updated_in_pangea_at=datetime.now(UTC),
    )
    session.add(model)
    session.commit()
    session.refresh(model)
    session.expunge(model)
    session.close()
    return model


class TestAddAnalysisPrecedentController:
    def test_should_return_201_and_add_analysis_precedent(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)
        precedent = _create_precedent(sqlalchemy_session_factory)

        response = client.post(
            f'/intake/analyses/{analysis.id}/precedents',
            json={
                'court': precedent.court,
                'kind': precedent.kind,
                'number': precedent.number,
            },
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        analysis_precedent = inspection_session.scalar(
            select(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis.id,
                AnalysisPrecedentModel.precedent_id == precedent.id,
            )
        )
        inspection_session.close()

        assert response.status_code == 201
        response_body = response.json()
        assert response_body['analysis_id'] == analysis.id
        assert response_body['precedent']['id'] == precedent.id
        assert response_body['is_chosen'] is True
        assert response_body['is_manually_added'] is True
        assert analysis_precedent is not None
        assert analysis_precedent.is_chosen is True
        assert analysis_precedent.is_manually_added is True

    def test_should_return_422_when_identifier_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.post(
            f'/intake/analyses/{analysis.id}/precedents',
            json={},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
