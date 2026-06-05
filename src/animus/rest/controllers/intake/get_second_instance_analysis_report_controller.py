from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.structures.dtos import SecondInstanceAnalysisReportDto
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    SecondInstanceDecisionsRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import GetSecondInstanceAnalysisReportUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class GetSecondInstanceAnalysisReportController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/second-instance-report',
            status_code=200,
            response_model=SecondInstanceAnalysisReportDto,
        )
        @router.get(
            '/analyses/{analysis_id}/reports/second-instance',
            status_code=200,
            response_model=SecondInstanceAnalysisReportDto,
        )
        def _(
            analysis_id: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            analysis_documents_repository: Annotated[
                AnalysisDocumentsRepository,
                Depends(DatabasePipe.get_analysis_documents_repository_from_request),
            ],
            case_summaries_repository: Annotated[
                CaseSummariesRepository,
                Depends(DatabasePipe.get_case_summaries_repository_from_request),
            ],
            second_instance_decisions_repository: Annotated[
                SecondInstanceDecisionsRepository,
                Depends(
                    DatabasePipe.get_second_instance_decisions_repository_from_request
                ),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
            judgment_drafts_repository: Annotated[
                SecondInstanceJudgmentDraftsRepository,
                Depends(DatabasePipe.get_judgment_drafts_repository_from_request),
            ],
        ) -> SecondInstanceAnalysisReportDto:
            use_case = GetSecondInstanceAnalysisReportUseCase(
                analyses_repository=analyses_repository,
                analysis_documents_repository=analysis_documents_repository,
                case_summaries_repository=case_summaries_repository,
                second_instance_decisions_repository=second_instance_decisions_repository,
                analysis_precedents_repository=analysis_precedents_repository,
                judgment_drafts_repository=judgment_drafts_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id.value,
            )
