from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    CaseAssessmentBriefingModel,
    CaseSummaryModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import (
    BuildAuthHeadersFixture,
    CreateAnalysisFixture,
)


def _persist_case_assessment_briefing(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
    legal_area: str = 'CIVIL',
    court_jurisdiction: str = 'TJSP',
    main_claims: str = 'Pedido principal original',
    intended_thesis: str = 'Tese principal original',
) -> None:
    session = sqlalchemy_session_factory()
    session.add(
        CaseAssessmentBriefingModel(
            analysis_id=analysis_id,
            legal_area=legal_area,
            court_jurisdiction=court_jurisdiction,
            main_claims=main_claims,
            intended_thesis=intended_thesis,
            created_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
            updated_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
        )
    )
    session.commit()
    session.close()


def _persist_case_summary(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
) -> None:
    session = sqlalchemy_session_factory()
    session.add(
        CaseSummaryModel(
            analysis_id=analysis_id,
            case_summary='Resumo existente',
            legal_issue='Questão jurídica existente',
            central_question='Pergunta central existente',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['Termo 1'],
        )
    )
    session.commit()
    session.close()


class TestCreateCaseAssessmentBriefingController:
    def test_should_return_201_and_persist_briefing_when_payload_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-assessment-briefing',
            json={
                'legal_area': 'CIVIL',
                'court_jurisdiction': 'TJSP',
                'main_claims': 'Reconhecimento da nulidade contratual',
                'intended_thesis': 'Aplicação do CDC ao contrato discutido',
            },
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_briefing = inspection_session.scalar(
            select(CaseAssessmentBriefingModel).where(
                CaseAssessmentBriefingModel.analysis_id == analysis.id
            )
        )
        persisted_analysis = inspection_session.scalar(
            select(AnalysisModel).where(AnalysisModel.id == analysis.id)
        )
        inspection_session.close()

        assert response.status_code == 201
        assert persisted_briefing is not None
        assert persisted_analysis is not None
        assert (
            persisted_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_briefing_submitted().dto
        )
        assert response.json() == {
            'analysis_id': analysis.id,
            'legal_area': 'CIVIL',
            'court_jurisdiction': 'TJSP',
            'main_claims': 'Reconhecimento da nulidade contratual',
            'intended_thesis': 'Aplicação do CDC ao contrato discutido',
        }

    def test_should_return_201_replace_briefing_and_remove_existing_case_summary_when_resubmitting(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_case_analyzed().dto,
        )
        _persist_case_assessment_briefing(
            sqlalchemy_session_factory,
            analysis_id=analysis.id,
        )
        _persist_case_summary(
            sqlalchemy_session_factory,
            analysis_id=analysis.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-assessment-briefing',
            json={
                'legal_area': 'TRABALHISTA',
                'court_jurisdiction': 'TRT2',
                'main_claims': 'Horas extras e reflexos',
                'intended_thesis': 'Controle de jornada inválido',
            },
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_briefing = inspection_session.scalar(
            select(CaseAssessmentBriefingModel).where(
                CaseAssessmentBriefingModel.analysis_id == analysis.id
            )
        )
        persisted_case_summary = inspection_session.scalar(
            select(CaseSummaryModel).where(CaseSummaryModel.analysis_id == analysis.id)
        )
        persisted_analysis = inspection_session.scalar(
            select(AnalysisModel).where(AnalysisModel.id == analysis.id)
        )
        inspection_session.close()

        assert response.status_code == 201
        assert persisted_briefing is not None
        assert persisted_briefing.legal_area == 'TRABALHISTA'
        assert persisted_briefing.court_jurisdiction == 'TRT2'
        assert persisted_briefing.main_claims == 'Horas extras e reflexos'
        assert persisted_briefing.intended_thesis == 'Controle de jornada inválido'
        assert persisted_case_summary is None
        assert persisted_analysis is not None
        assert (
            persisted_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_briefing_submitted().dto
        )
        assert response.json() == {
            'analysis_id': analysis.id,
            'legal_area': 'TRABALHISTA',
            'court_jurisdiction': 'TRT2',
            'main_claims': 'Horas extras e reflexos',
            'intended_thesis': 'Controle de jornada inválido',
        }

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        authenticated_account = create_account(is_verified=True, is_active=True)
        owner_account = create_account(
            email='owner@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(
            account_id=owner_account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-assessment-briefing',
            json={
                'legal_area': 'CIVIL',
                'court_jurisdiction': 'TJSP',
                'main_claims': 'Pedido principal',
                'intended_thesis': 'Tese principal',
            },
            headers=build_auth_headers(authenticated_account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_briefing = inspection_session.scalar(
            select(CaseAssessmentBriefingModel).where(
                CaseAssessmentBriefingModel.analysis_id == analysis.id
            )
        )
        inspection_session.close()

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Análise nao pertence a conta autenticada',
        }
        assert persisted_briefing is None

    def test_should_return_400_when_analysis_type_is_not_case_assessment(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-assessment-briefing',
            json={
                'legal_area': 'CIVIL',
                'court_jurisdiction': 'TJSP',
                'main_claims': 'Pedido principal',
                'intended_thesis': 'Tese principal',
            },
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_briefing = inspection_session.scalar(
            select(CaseAssessmentBriefingModel).where(
                CaseAssessmentBriefingModel.analysis_id == analysis.id
            )
        )
        inspection_session.close()

        assert response.status_code == 400
        assert response.json() == {
            'title': 'Erro de validação',
            'message': 'Tipo de análise incoerente',
        }
        assert persisted_briefing is None

    def test_should_return_422_when_intended_thesis_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-assessment-briefing',
            json={
                'legal_area': 'CIVIL',
                'court_jurisdiction': 'TJSP',
                'main_claims': 'Pedido principal',
            },
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422

    def test_should_return_400_when_main_claims_is_blank(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_waiting_briefing().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-assessment-briefing',
            json={
                'legal_area': 'CIVIL',
                'court_jurisdiction': 'TJSP',
                'main_claims': '   ',
                'intended_thesis': 'Tese principal',
            },
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 400
        assert response.json() == {
            'title': 'Erro de validação',
            'message': 'Pedido principal obrigatorio',
        }
