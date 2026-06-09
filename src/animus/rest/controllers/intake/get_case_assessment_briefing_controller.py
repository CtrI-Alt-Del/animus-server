from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos import CaseAssessmentBriefingDto
from animus.core.intake.interfaces import CaseAssessmentBriefingsRepository
from animus.core.intake.use_cases import GetCaseAssessmentBriefingUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class GetCaseAssessmentBriefingController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/case-assessment-briefing',
            status_code=200,
            response_model=CaseAssessmentBriefingDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            case_assessment_briefings_repository: Annotated[
                CaseAssessmentBriefingsRepository,
                Depends(
                    DatabasePipe.get_case_assessment_briefings_repository_from_request,
                ),
            ],
        ) -> CaseAssessmentBriefingDto:
            use_case = GetCaseAssessmentBriefingUseCase(
                case_assessment_briefings_repository=(
                    case_assessment_briefings_repository
                ),
            )

            return use_case.execute(analysis_id=analysis.id.value)
