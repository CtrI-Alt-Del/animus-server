from animus.core.intake.domain.errors.analysis_document_not_found_error import (
    AnalysisDocumentNotFoundError,
)
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.domain.errors.case_assessment_briefing_not_found_error import (
    CaseAssessmentBriefingNotFoundError,
)
from animus.core.intake.domain.errors.case_summary_unavailable_error import (
    CaseSummaryUnavailableError,
)
from animus.core.intake.domain.errors.petition_draft_unavailable_error import (
    PetitionDraftUnavailableError,
)
from animus.core.intake.domain.structures.case_assessment_analysis_report import (
    CaseAssessmentAnalysisReport,
)
from animus.core.intake.domain.structures.dtos.case_assessment_analysis_report_dto import (
    CaseAssessmentAnalysisReportDto,
)
from animus.core.intake.interfaces.analysis_documents_repository import (
    AnalysisDocumentsRepository,
)
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.intake.interfaces.case_assessment_briefings_repository import (
    CaseAssessmentBriefingsRepository,
)
from animus.core.intake.interfaces.case_summaries_repository import (
    CaseSummariesRepository,
)
from animus.core.intake.interfaces.petition_drafts_repository import (
    PetitionDraftsRepository,
)
from animus.core.shared.domain.errors.forbidden_error import ForbiddenError
from animus.core.shared.domain.structures import Id


class GetCaseAssessmentAnalysisReportUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        case_assessment_briefings_repository: CaseAssessmentBriefingsRepository,
        analysis_documents_repository: AnalysisDocumentsRepository,
        case_summaries_repository: CaseSummariesRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        petition_drafts_repository: PetitionDraftsRepository,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._case_assessment_briefings_repository = (
            case_assessment_briefings_repository
        )
        self._analysis_documents_repository = analysis_documents_repository
        self._case_summaries_repository = case_summaries_repository
        self._analysis_precedents_repository = analysis_precedents_repository
        self._petition_drafts_repository = petition_drafts_repository

    def execute(
        self, analysis_id: str, account_id: str
    ) -> CaseAssessmentAnalysisReportDto:
        id_analysis = Id.create(analysis_id)
        id_account = Id.create(account_id)

        analysis = self._analyses_repository.find_by_id(id_analysis)

        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.account_id != id_account:
            raise ForbiddenError('Esta analise nao pertence a sua conta.')

        briefing = self._case_assessment_briefings_repository.find_by_analysis_id(
            id_analysis
        )
        if briefing is None:
            raise CaseAssessmentBriefingNotFoundError

        document = self._analysis_documents_repository.find_by_analysis_id(id_analysis)
        if document is None:
            raise AnalysisDocumentNotFoundError

        case_summary = self._case_summaries_repository.find_by_analysis_id(id_analysis)
        if case_summary is None:
            raise CaseSummaryUnavailableError

        petition_draft = self._petition_drafts_repository.find_by_analysis_id(
            id_analysis
        )
        if petition_draft is None:
            raise PetitionDraftUnavailableError

        precedents = [
            p
            for p in self._analysis_precedents_repository.find_many_by_analysis_id(
                id_analysis
            ).items
            if p.is_chosen.is_true
        ]

        report = CaseAssessmentAnalysisReport(
            analysis=analysis,
            briefing=briefing,
            document=document,
            case_summary=case_summary,
            precedents=precedents,
            petition_draft=petition_draft,
        )

        return report.dto
