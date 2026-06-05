from animus.core.intake.domain.errors import (
    AnalysisDocumentNotFoundError,
    AnalysisNotFoundError,
    CaseSummaryNotFoundError,
    SecondInstanceDecisionNotFoundError,
)
from animus.core.intake.domain.structures import SecondInstanceAnalysisReport
from animus.core.intake.domain.structures.dtos import (
    SecondInstanceAnalysisReportDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    SecondInstanceDecisionsRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.shared.domain.errors.forbidden_error import ForbiddenError
from animus.core.shared.domain.structures import Id


class GetSecondInstanceAnalysisReportUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        analysis_documents_repository: AnalysisDocumentsRepository,
        case_summaries_repository: CaseSummariesRepository,
        second_instance_decisions_repository: SecondInstanceDecisionsRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        judgment_drafts_repository: SecondInstanceJudgmentDraftsRepository
        | None = None,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._analysis_documents_repository = analysis_documents_repository
        self._case_summaries_repository = case_summaries_repository
        self._second_instance_decisions_repository = (
            second_instance_decisions_repository
        )
        self._analysis_precedents_repository = analysis_precedents_repository
        self._judgment_drafts_repository = judgment_drafts_repository

    def execute(
        self, analysis_id: str, account_id: str
    ) -> SecondInstanceAnalysisReportDto:
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
            raise CaseSummaryNotFoundError

        second_instance_decision = (
            self._second_instance_decisions_repository.find_by_analysis_id(
                id_analysis,
            )
        )
        if second_instance_decision is None:
            raise SecondInstanceDecisionNotFoundError

        analysis_precedents = (
            self._analysis_precedents_repository.find_many_by_analysis_id(id_analysis)
        )

        classified_precedents = [
            p for p in analysis_precedents.items if p.is_chosen.is_true
        ]
        judgment_draft = None
        if self._judgment_drafts_repository is not None:
            judgment_draft = self._judgment_drafts_repository.find_by_analysis_id(
                id_analysis,
            )

        report = SecondInstanceAnalysisReport(
            analysis=analysis,
            document=document,
            case_summary=case_summary,
            second_instance_decision=second_instance_decision,
            precedents=classified_precedents,
            draft=judgment_draft,
        )

        return report.dto
