from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos import AnalysisStatusDto
from animus.pipes.intake_pipe import IntakePipe


class GetAnalysisStatusController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            "/analyses/{analysis_id}/status",
            status_code=200,
            response_model=AnalysisStatusDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
        ) -> AnalysisStatusDto:
            return analysis.status.dto
