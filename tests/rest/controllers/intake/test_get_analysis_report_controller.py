from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.database.sqlalchemy.models.intake import (
    AnalysisDocumentModel,
    AnalysisModel,
    AnalysisPrecedentModel,
    CaseSummaryModel,
    JudgmentDraftModel,
    PetitionDraftModel,
    PrecedentModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_report_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
    analysis_type: AnalysisType,
    with_case_summary: bool = True,
    with_petition_draft: bool = False,
    with_judgment_draft: bool = False,
) -> str:
    analysis_id = str(ULID())
    precedent_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise completa',
            folder_id=None,
            account_id=account_id,
            type=analysis_type.value,
            status='DONE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        AnalysisDocumentModel(
            analysis_id=analysis_id,
            uploaded_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
            document_file_path='analyses/document.pdf',
            document_name='document.pdf',
        )
    )
    if with_case_summary:
        session.add(
            CaseSummaryModel(
                analysis_id=analysis_id,
                case_summary='Resumo',
                legal_issue='Questao',
                central_question='Pergunta',
                relevant_laws=['Lei'],
                key_facts=['Fato'],
                search_terms=['Termo'],
            )
        )
    if with_petition_draft:
        session.add(
            PetitionDraftModel(
                analysis_id=analysis_id,
                content='Minuta de peticao',
            )
        )
    if with_judgment_draft:
        session.add(
            JudgmentDraftModel(
                analysis_id=analysis_id,
                content='Minuta de julgamento',
            )
        )
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STF',
            kind='SV',
            number=123,
            status='Vigente',
            enunciation='Enunciado',
            thesis='Tese',
            last_updated_in_pangea_at=datetime.now(UTC),
        )
    )
    session.add(
        AnalysisPrecedentModel(
            analysis_id=analysis_id,
            precedent_id=precedent_id,
            is_chosen=True,
            similarity_score=90.0,
            synthesis='Sintese',
        )
    )
    session.commit()
    session.close()

    return analysis_id


class TestGetSecondInstanceAnalysisReportController:
    def test_should_return_200_when_second_instance_analysis_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_report_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            analysis_type=AnalysisType.SECOND_INSTANCE,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/second-instance-report',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload['analysis']['type'] == AnalysisType.SECOND_INSTANCE.value
        assert payload['document']['analysis_id'] == analysis_id
        assert payload['case_summary']['case_summary'] == 'Resumo'
        assert payload['chosen_precedent']['analysis_id'] == analysis_id


class TestGetCaseAssessmentAnalysisReportController:
    def test_should_return_200_when_case_assessment_analysis_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_report_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            analysis_type=AnalysisType.CASE_ASSESSMENT,
            with_petition_draft=True,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/case-assessment-report',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload['analysis']['type'] == AnalysisType.CASE_ASSESSMENT.value
        assert payload['petition_draft'] == {
            'analysis_id': analysis_id,
            'content': 'Minuta de peticao',
        }
        assert payload['chosen_precedent'] is not None
        assert payload['chosen_precedent']['is_chosen'] is True


class TestGetFirstInstanceAnalysisReportController:
    def test_should_return_200_when_first_instance_analysis_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_report_analysis(
            sqlalchemy_session_factory,
            account_id=account.id,
            analysis_type=AnalysisType.FIRST_INSTANCE,
            with_judgment_draft=True,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/first-instance-report',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload['analysis']['type'] == AnalysisType.FIRST_INSTANCE.value
        assert payload['judgment_draft'] == {
            'analysis_id': analysis_id,
            'content': 'Minuta de julgamento',
        }
