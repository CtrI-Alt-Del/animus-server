from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    PetitionModel,
    PetitionSummaryModel,
)
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


def _build_auth_headers(account_id: str) -> dict[str, str]:
    access_token = JoseJwtProvider().encode(Text.create(account_id)).access_token.value
    return {'Authorization': f'Bearer {access_token}'}


def _create_analysis_with_petition_summary(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> tuple[str, str]:
    analysis_id = str(ULID())
    petition_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise de precedentes',
            folder_id=None,
            account_id=account_id,
            status=AnalysisStatusValue.WAITING_PETITION.value,
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

    return analysis_id, petition_id


class TestListAnalysisPetitionsController:
    def test_should_return_200_and_analysis_petitions_payload_when_analysis_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id, petition_id = _create_analysis_with_petition_summary(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/petitions',
            headers=_build_auth_headers(account.id),
        )

        response_payload = response.json()

        assert response.status_code == 200
        assert len(response_payload['items']) == 1
        assert response_payload['items'][0]['petition'] == {
            'id': petition_id,
            'analysis_id': analysis_id,
            'uploaded_at': '2026-03-27T10:30:00+00:00',
            'document': {
                'file_path': 'petitions/initial-petition.pdf',
                'name': 'Peticao inicial.pdf',
            },
        }
        assert response_payload['items'][0]['summary'] == {
            'case_summary': 'Resumo objetivo da peticao inicial',
            'legal_issue': 'Controversia sobre inadimplemento contratual',
            'central_question': 'Ha inadimplemento apto a justificar condenacao?',
            'relevant_laws': ['Codigo Civil, Art. 389'],
            'key_facts': ['Contrato firmado e nao adimplido'],
            'search_terms': ['inadimplemento contratual'],
            'type_of_action': None,
            'secondary_legal_issues': [],
            'alternative_questions': [],
            'jurisdiction_issue': None,
            'standing_issue': None,
            'requested_relief': [],
            'procedural_issues': [],
            'excluded_or_accessory_topics': [],
        }

    def test_should_return_422_when_analysis_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses/invalid-analysis-id/petitions',
            headers=_build_auth_headers(account.id),
        )

        assert response.status_code == 422
