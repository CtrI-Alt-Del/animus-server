from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.structures.dtos import CaseAssessmentBriefingDto
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseAssessmentBriefingsRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import CreateCaseAssessmentBriefingUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class _Body(BaseModel):
    legal_area: str
    court_jurisdiction: str
    main_claims: str
    intended_thesis: str


class CreateCaseAssessmentBriefingController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/case-assessment-briefing',
            status_code=201,
            response_model=CaseAssessmentBriefingDto,
        )
        def _(
            analysis_id: str,
            body: _Body,
            _: Annotated[
                object,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            case_assessment_briefings_repository: Annotated[
                CaseAssessmentBriefingsRepository,
                Depends(
                    DatabasePipe.get_case_assessment_briefings_repository_from_request
                ),
            ],
            case_summaries_repository: Annotated[
                CaseSummariesRepository,
                Depends(DatabasePipe.get_case_summaries_repository_from_request),
            ],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
        ) -> CaseAssessmentBriefingDto:
            use_case = CreateCaseAssessmentBriefingUseCase(
                case_assessment_briefings_repository=case_assessment_briefings_repository,
                case_summaries_repository=case_summaries_repository,
                analyses_repository=analyses_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                legal_area=body.legal_area,
                court_jurisdiction=body.court_jurisdiction,
                main_claims=body.main_claims,
                intended_thesis=body.intended_thesis,
            )
