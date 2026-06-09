from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis, AnalysisType
from animus.core.intake.domain.entities.dtos import PrecedentDto
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.domain.errors.case_assessment_briefing_not_found_error import (
    CaseAssessmentBriefingNotFoundError,
)
from animus.core.intake.domain.errors.second_instance_decision_not_found_error import (
    SecondInstanceDecisionNotFoundError,
)
from animus.core.intake.domain.errors.petition_draft_unavailable_error import (
    PetitionDraftUnavailableError,
)
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.case_assessment_briefing import (
    CaseAssessmentBriefing,
)
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.domain.structures.second_instance_decision import (
    SecondInstanceDecision,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.intake.domain.structures.dtos import (
    AnalysisDocumentDto,
    AnalysisPrecedentDto,
    CaseAssessmentBriefingDto,
    CaseSummaryDto,
    SecondInstanceDecisionDto,
    SecondInstanceJudgmentDraftDto,
    PetitionDraftDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseAssessmentBriefingsRepository,
    CaseSummariesRepository,
    SecondInstanceDecisionsRepository,
)
from animus.core.intake.interfaces.judgment_drafts_repository import (
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.interfaces.petition_drafts_repository import (
    PetitionDraftsRepository,
)
from animus.core.intake.use_cases.get_case_assessment_analysis_report_use_case import (
    GetCaseAssessmentAnalysisReportUseCase,
)
from animus.core.intake.use_cases.get_first_instance_analysis_report_use_case import (
    GetFirstInstanceAnalysisReportUseCase,
)
from animus.core.intake.use_cases.get_second_instance_analysis_report_use_case import (
    GetSecondInstanceAnalysisReportUseCase,
)
from animus.core.shared.domain.errors.forbidden_error import ForbiddenError
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker


def _make_analysis(
    *, analysis_id: str, account_id: str, analysis_type: AnalysisType
) -> Analysis:
    return Analysis.create(
        AnalysisDto(
            id=analysis_id,
            name='Análise',
            account_id=account_id,
            status='DONE',
            created_at='2026-04-04T10:00:00Z',
            type=analysis_type.dto,
        )
    )


class TestGetCaseAssessmentAnalysisReportUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository, instance=True
        )
        self.case_assessment_briefings_repository_mock = create_autospec(
            CaseAssessmentBriefingsRepository, instance=True
        )
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository, instance=True
        )
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository, instance=True
        )
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository, instance=True
        )
        self.petition_drafts_repository_mock = create_autospec(
            PetitionDraftsRepository, instance=True
        )
        self.use_case = GetCaseAssessmentAnalysisReportUseCase(
            analyses_repository=self.analyses_repository_mock,
            case_assessment_briefings_repository=self.case_assessment_briefings_repository_mock,
            analysis_documents_repository=self.analysis_documents_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            petition_drafts_repository=self.petition_drafts_repository_mock,
        )

    def test_should_return_case_assessment_analysis_report_with_petition_draft(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = _make_analysis(
            analysis_id=analysis_id,
            account_id=account_id,
            analysis_type=AnalysisType.create_as_case_assessment(),
        )
        briefing = CaseAssessmentBriefing.create(
            CaseAssessmentBriefingDto(
                analysis_id=analysis_id,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='Pedidos principais',
                intended_thesis='Tese pretendida',
            )
        )
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-04-04T10:00:00Z',
                file_path='path/to/file.pdf',
                name='file.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questão legal',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )
        petition_draft = PetitionDraft.create(
            PetitionDraftDto(
                analysis_id=analysis_id,
                structured_facts='Fatos estruturados',
                legal_grounds='Fundamentos jurídicos',
                central_thesis='Tese central',
                requests=['Pedido 1'],
                precedent_citations=['STJ REsp 123 - tese aplicável'],
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = briefing
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            petition_draft
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[]
        )

        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        assert result.analysis == analysis.dto
        assert result.briefing == briefing.dto
        assert result.document == document.dto
        assert result.case_summary == case_summary.dto
        assert result.petition_draft == petition_draft.dto

    def test_should_raise_petition_draft_unavailable_error_when_petition_draft_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = _make_analysis(
            analysis_id=analysis_id,
            account_id=account_id,
            analysis_type=AnalysisType.create_as_case_assessment(),
        )
        briefing = CaseAssessmentBriefing.create(
            CaseAssessmentBriefingDto(
                analysis_id=analysis_id,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='Pedidos principais',
                intended_thesis='Tese pretendida',
            )
        )
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-04-04T10:00:00Z',
                file_path='path/to/file.pdf',
                name='file.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questão legal',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = briefing
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(PetitionDraftUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

    def test_should_raise_case_assessment_briefing_not_found_error_when_briefing_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = _make_analysis(
            analysis_id=analysis_id,
            account_id=account_id,
            analysis_type=AnalysisType.create_as_case_assessment(),
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(CaseAssessmentBriefingNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)


class TestGetFirstInstanceAnalysisReportUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository, instance=True
        )
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository, instance=True
        )
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository, instance=True
        )
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository, instance=True
        )
        self.use_case = GetFirstInstanceAnalysisReportUseCase(
            analyses_repository=self.analyses_repository_mock,
            analysis_documents_repository=self.analysis_documents_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
        )

    def test_should_return_first_instance_analysis_report(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = _make_analysis(
            analysis_id=analysis_id,
            account_id=account_id,
            analysis_type=AnalysisType.create_as_first_instance(),
        )
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-04-04T10:00:00Z',
                file_path='path/to/file.pdf',
                name='file.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questão legal',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[]
        )

        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        assert result.analysis == analysis.dto
        assert result.document == document.dto
        assert result.case_summary == case_summary.dto


class TestGetSecondInstanceAnalysisReportUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository, instance=True
        )
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository, instance=True
        )
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository, instance=True
        )
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository, instance=True
        )
        self.second_instance_decisions_repository_mock = create_autospec(
            SecondInstanceDecisionsRepository, instance=True
        )
        self.judgment_drafts_repository_mock = create_autospec(
            SecondInstanceJudgmentDraftsRepository, instance=True
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None
        self.use_case = GetSecondInstanceAnalysisReportUseCase(
            analyses_repository=self.analyses_repository_mock,
            analysis_documents_repository=self.analysis_documents_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            second_instance_decisions_repository=self.second_instance_decisions_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            judgment_drafts_repository=self.judgment_drafts_repository_mock,
        )

    def test_should_return_analysis_report_dto_without_draft_when_draft_does_not_exist(
        self,
    ) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(analysis_id=analysis_id, account_id=account_id)
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-04-04T10:00:00Z',
                file_path='path/to/file.pdf',
                name='file.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questão legal',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )
        decision = SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=analysis_id,
                description='Dar parcial provimento ao recurso',
            )
        )

        precedent_1 = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=PrecedentDto(
                    id=Id.create().value,
                    identifier=PrecedentIdentifierDto(court='STF', kind='RG', number=1),
                    status='vigente',
                    enunciation='E1',
                    thesis='T1',
                    last_updated_in_pangea_at='2026-04-04T10:00:00Z',
                ),
                similarity_score=90.0,
                is_chosen=True,
                synthesis='S1',
            )
        )
        precedent_2 = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=PrecedentDto(
                    id=Id.create().value,
                    identifier=PrecedentIdentifierDto(court='STF', kind='RG', number=2),
                    status='vigente',
                    enunciation='E2',
                    thesis='T2',
                    last_updated_in_pangea_at='2026-04-04T10:00:00Z',
                ),
                similarity_score=75.0,
                is_chosen=False,
                synthesis='S2',
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = decision
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[precedent_1, precedent_2]
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None

        # Act
        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        # Assert
        assert result.analysis == analysis.dto
        assert result.document == document.dto
        assert result.case_summary == case_summary.dto
        assert result.second_instance_decision == decision.dto()
        assert len(result.precedents) == 1
        assert result.precedents[0].precedent.id == precedent_1.precedent.id.value
        assert result.precedents[0].is_chosen is True
        assert result.draft is None

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.analysis_documents_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )

    def test_should_return_analysis_report_dto_with_draft_when_draft_exists(
        self,
    ) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(analysis_id=analysis_id, account_id=account_id)
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-04-04T10:00:00Z',
                file_path='path/to/file.pdf',
                name='file.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questão legal',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )
        decision = SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=analysis_id,
                description='Negar provimento ao recurso',
            )
        )
        judgment_draft = SecondInstanceJudgmentDraft.create(
            SecondInstanceJudgmentDraftDto(
                analysis_id=analysis_id,
                report='Relatório',
                merit_analysis='Fundamentação',
                precedent_adherence_analysis='Aderência',
                ruling=['Dispositivo'],
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = decision
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[]
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            judgment_draft
        )

        # Act
        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        # Assert
        assert result.draft == judgment_draft.dto
        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )

    def test_should_raise_forbidden_error_when_account_id_does_not_match(self) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value
        wrong_account_id = Id.create().value
        analysis = AnalysesFaker.fake(analysis_id=analysis_id, account_id=account_id)

        self.analyses_repository_mock.find_by_id.return_value = analysis

        # Act & Assert
        with pytest.raises(ForbiddenError):
            self.use_case.execute(analysis_id=analysis_id, account_id=wrong_account_id)

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value

        self.analyses_repository_mock.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

    def test_should_raise_second_instance_decision_not_found_error_when_decision_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=account_id,
            type=AnalysisType.create_as_second_instance().dto,
            status='DONE',
        )
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-04-04T10:00:00Z',
                file_path='path/to/file.pdf',
                name='file.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questão legal',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(SecondInstanceDecisionNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

    def test_should_return_empty_precedents_when_none_are_chosen(self) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(analysis_id=analysis_id, account_id=account_id)
        document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-04-04T10:00:00Z',
                file_path='path/to/file.pdf',
                name='file.pdf',
            )
        )
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questão legal',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )
        decision = SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=analysis_id,
                description='Negar provimento ao recurso',
            )
        )

        def create_precedent(percentage: float | None) -> AnalysisPrecedent:
            return AnalysisPrecedent.create(
                AnalysisPrecedentDto(
                    analysis_id=analysis_id,
                    precedent=PrecedentDto(
                        id=Id.create().value,
                        identifier=PrecedentIdentifierDto(
                            court='STF', kind='RG', number=int(percentage or 0)
                        ),
                        status='vigente',
                        enunciation='E',
                        thesis='T',
                        last_updated_in_pangea_at='2026-04-04T10:00:00Z',
                    ),
                    similarity_score=percentage,
                    is_chosen=False,
                    synthesis='S',
                )
            )

        precedents = [
            create_precedent(85.0),
            create_precedent(84.9),
            create_precedent(70.0),
            create_precedent(69.9),
            create_precedent(None),
        ]

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            document
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = decision
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=precedents
        )

        # Act
        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        # Assert
        assert result.precedents == []
