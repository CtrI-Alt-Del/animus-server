from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.shared.domain.structures import Id, Text
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_analisyses_repository import (
    SqlalchemyAnalisysesRepository,
)
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_petitions_repository import (
    SqlalchemyPetitionsRepository,
)
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker
from animus.fakers.intake.entities.petitions_faker import PetitionsFaker
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient


def _make_access_token(account_id: str) -> str:
    session = JoseJwtProvider().encode(Text.create(account_id))
    return session.access_token.value


def _create_analysis_and_petition(
    sqlalchemy_session_factory: sessionmaker[Session],
    account_id: str,
) -> tuple[str, str, str]:
    analysis = AnalysesFaker.fake(account_id=account_id)
    petition = PetitionsFaker.fake(
        analysis_id=analysis.id.value,
        document=PetitionDocumentDto(
            file_path='intake/analyses/01TEST/petitions/petition.pdf',
            name='petition.pdf',
        ),
    )
    session = sqlalchemy_session_factory()
    analyses_repository = SqlalchemyAnalisysesRepository(session)
    petitions_repository = SqlalchemyPetitionsRepository(session)

    analyses_repository.add(analysis)
    petitions_repository.add(petition)
    session.commit()
    session.close()

    return account_id, analysis.id.value, petition.id.value


class TestSummarizePetitionController:
    def test_should_return_202_publish_event_and_update_analysis_status(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        access_token = _make_access_token(account.id)
        _, analysis_id, petition_id = _create_analysis_and_petition(
            sqlalchemy_session_factory,
            account.id,
        )
        app = client.app
        assert isinstance(app, FastAPI)

        response = client.post(
            f'/intake/petitions/{petition_id}/summary',
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 202
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name
            == 'intake/petition.summary.requested'
        )
        assert fake_inngest_client.sent_events[0].data['petition_id'] == petition_id

        session = sqlalchemy_session_factory()
        analysis = SqlalchemyAnalisysesRepository(session).find_by_id(
            Id.create(analysis_id)
        )
        session.close()

        assert analysis is not None
        assert analysis.status.value == AnalysisStatusValue.ANALYZING_PETITION

    def test_should_return_404_when_petition_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        access_token = _make_access_token(account.id)

        response = client.post(
            '/intake/petitions/01ARZ3NDEKTSV4RRFFQ69G5FAV/summary',
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Peticao nao encontrada',
        }
        assert len(fake_inngest_client.sent_events) == 0
