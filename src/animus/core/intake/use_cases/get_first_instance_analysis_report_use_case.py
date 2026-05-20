from animus.core.intake.domain.errors.analysis_document_not_found_error import (
    AnalysisDocumentNotFoundError,
)
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.domain.errors.case_summary_unavailable_error import (
    CaseSummaryUnavailableError,
)
from animus.core.intake.domain.errors.judgment_draft_unavailable_error import (
    SecondInstanceJudgmentDraftUnavailableError,
)
from animus.core.intake.domain.structures.dtos.first_instance_analysis_report_dto import (
    FirstInstanceAnalysisReportDto,
)
from animus.core.intake.domain.structures.first_instance_analysis_report import (
    FirstInstanceAnalysisReport,
)
from animus.core.intake.interfaces.analysis_documents_repository import (
    AnalysisDocumentsRepository,
)
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.intake.interfaces.case_summaries_repository import (
    CaseSummariesRepository,
)
from animus.core.intake.interfaces.judgment_drafts_repository import (
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.shared.domain.errors.forbidden_error import ForbiddenError
from animus.core.shared.domain.structures import Id


class GetFirstInstanceAnalysisReportUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        analysis_documents_repository: AnalysisDocumentsRepository,
        case_summaries_repository: CaseSummariesRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        judgment_drafts_repository: SecondInstanceJudgmentDraftsRepository,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._analysis_documents_repository = analysis_documents_repository
        self._case_summaries_repository = case_summaries_repository
        self._analysis_precedents_repository = analysis_precedents_repository
        self._judgment_drafts_repository = judgment_drafts_repository

    def execute(
        self, analysis_id: str, account_id: str
    ) -> FirstInstanceAnalysisReportDto:
        id_analysis = Id.create(analysis_id)
        id_account = Id.create(account_id)

        analysis = self._analyses_repository.find_by_id(id_analysis)

        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.account_id != id_account:
            raise ForbiddenError('Esta analise nao pertence a sua conta.')

        document = self._analysis_documents_repository.find_by_analysis_id(id_analysis)
        if document is None:
            raise AnalysisDocumentNotFoundError

        case_summary = self._case_summaries_repository.find_by_analysis_id(id_analysis)
        if case_summary is None:
            raise CaseSummaryUnavailableError

        judgment_draft = self._judgment_drafts_repository.find_by_analysis_id(
            id_analysis
        )
        if judgment_draft is None:
            raise SecondInstanceJudgmentDraftUnavailableError

        precedents = self._analysis_precedents_repository.find_many_by_analysis_id(
            id_analysis
        ).items

        report = FirstInstanceAnalysisReport(
            analysis=analysis,
            document=document,
            case_summary=case_summary,
            precedents=precedents,
            judgment_draft=judgment_draft,
        )

        return report.dto
