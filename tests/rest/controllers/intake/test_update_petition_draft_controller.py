from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.database.sqlalchemy.models.intake import AnalysisModel, PetitionDraftModel
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
            name='Análise com minuta editável',
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
                structured_facts='Fatos originais',
                legal_grounds='Fundamentos originais',
                central_thesis='Tese original',
                requests=['Pedido original'],
                precedent_citations=['Precedente original'],
            )
        )
    session.commit()
    session.close()

    return analysis_id


def _build_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        'structured_facts': '  Fatos atualizados com espacos  ',
        'legal_grounds': '  Fundamentos atualizados com espacos  ',
        'central_thesis': '  Tese atualizada com espacos  ',
        'requests': ['  Pedido 1  ', 'Pedido 2'],
        'precedent_citations': ['  Precedente 1  ', 'Precedente 2'],
    }
    payload.update(overrides)
    return payload


class TestUpdatePetitionDraftController:
    def test_should_return_200_and_persist_payload_without_trimming_content(
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
        payload = _build_payload()

        response = client.put(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
            json=payload,
        )

        assert response.status_code == 200
        assert response.json() == {'analysis_id': analysis_id, **payload}

        session = sqlalchemy_session_factory()
        petition_draft = session.get(PetitionDraftModel, analysis_id)

        assert petition_draft is not None
        assert petition_draft.structured_facts == payload['structured_facts']
        assert petition_draft.legal_grounds == payload['legal_grounds']
        assert petition_draft.central_thesis == payload['central_thesis']
        assert petition_draft.requests == payload['requests']
        assert petition_draft.precedent_citations == payload['precedent_citations']

        session.close()

        get_response = client.get(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
        )

        assert get_response.status_code == 200
        assert get_response.json() == {'analysis_id': analysis_id, **payload}

    def test_should_return_404_when_petition_draft_does_not_exist(
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

        response = client.put(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
            json=_build_payload(),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Minuta da petição indisponivel',
        }

    @pytest.mark.parametrize(
        ('payload', 'field_name'),
        [
            pytest.param(
                _build_payload(structured_facts='   '),
                'structured_facts',
                id='blank-structured-facts',
            ),
            pytest.param(
                _build_payload(legal_grounds='   '),
                'legal_grounds',
                id='blank-legal-grounds',
            ),
            pytest.param(
                _build_payload(central_thesis='   '),
                'central_thesis',
                id='blank-central-thesis',
            ),
            pytest.param(
                _build_payload(requests=[]),
                'requests',
                id='empty-requests',
            ),
            pytest.param(
                _build_payload(requests=['Pedido válido', '   ']),
                'requests',
                id='blank-request-item',
            ),
            pytest.param(
                _build_payload(precedent_citations=[]),
                'precedent_citations',
                id='empty-precedent-citations',
            ),
            pytest.param(
                _build_payload(precedent_citations=['Precedente válido', '   ']),
                'precedent_citations',
                id='blank-precedent-item',
            ),
        ],
    )
    def test_should_return_422_when_payload_contains_blank_or_empty_values(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        payload: dict[str, object],
        field_name: str,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            with_petition_draft=True,
        )

        response = client.put(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(account.id),
            json=payload,
        )

        assert response.status_code == 422
        assert any(
            error['loc'] == ['body', field_name] for error in response.json()['detail']
        )

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        owner_account = create_account(
            email='owner-update-draft@example.com',
            is_verified=True,
            is_active=True,
        )
        requester_account = create_account(
            email='requester-update-draft@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis_id = _create_case_assessment_analysis(
            sqlalchemy_session_factory,
            account_id=owner_account.id,
            with_petition_draft=True,
        )

        response = client.put(
            f'/intake/analyses/{analysis_id}/petition-drafts',
            headers=build_auth_headers(requester_account.id),
            json=_build_payload(),
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Análise nao pertence a conta autenticada',
        }
