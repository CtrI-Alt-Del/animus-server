from collections.abc import Callable
from datetime import UTC

from fastapi.testclient import TestClient

from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.database.sqlalchemy.models.intake import AnalysisModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


class TestListProcessingAnalysesController:
    def test_should_return_analyses_in_processing_for_authenticated_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        other_account = create_account(
            email='other-account@example.com',
            is_verified=True,
            is_active=True,
        )

        analysis_1 = create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FA1',
            name='Análise buscando precedentes',
            status=CaseAssessmentAnalysisStatus.create('SEARCHING_PRECEDENTS').dto,
        )

        analysis_2 = create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FA2',
            name='Análise similaridade',
            status=CaseAssessmentAnalysisStatus.create(
                'ANALYZING_PRECEDENTS_SIMILARITY'
            ).dto,
        )

        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FA3',
            name='Análise aguardando',
            status=CaseAssessmentAnalysisStatus.create_as_waiting_document_upload().dto,
        )

        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FA4',
            name='Análise arquivada',
            status=CaseAssessmentAnalysisStatus.create_as_generating_petition_draft().dto,
            is_archived=True,
        )

        create_analysis(
            account_id=other_account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FA5',
            name='Análise de outra conta',
            status=SecondInstanceAnalysisStatus.create_as_analyzing_case().dto,
        )

        response = client.get(
            '/intake/analyses/processing',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                'id': analysis_2.id,
                'name': 'Análise similaridade',
                'folder_id': None,
                'account_id': account.id,
                'type': 'FIRST_INSTANCE',
                'status': CaseAssessmentAnalysisStatus.create(
                    'ANALYZING_PRECEDENTS_SIMILARITY'
                ).dto,
                'is_archived': False,
                'precedents_search_filters': None,
                'created_at': analysis_2.created_at.replace(tzinfo=UTC).isoformat(),
            },
            {
                'id': analysis_1.id,
                'name': 'Análise buscando precedentes',
                'folder_id': None,
                'account_id': account.id,
                'type': 'FIRST_INSTANCE',
                'status': CaseAssessmentAnalysisStatus.create(
                    'SEARCHING_PRECEDENTS'
                ).dto,
                'is_archived': False,
                'precedents_search_filters': None,
                'created_at': analysis_1.created_at.replace(tzinfo=UTC).isoformat(),
            },
        ]

    def test_should_return_empty_list_when_no_analyses_in_processing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        create_analysis(
            account_id=account.id,
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FA1',
            name='Análise finalizada',
            status=CaseAssessmentAnalysisStatus.create_as_done().dto,
        )

        response = client.get(
            '/intake/analyses/processing',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_should_return_401_when_unauthenticated(
        self,
        client: TestClient,
    ) -> None:
        response = client.get('/intake/analyses/processing')

        assert response.status_code == 422
