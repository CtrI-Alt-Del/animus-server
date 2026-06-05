from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos import SecondInstanceDecisionDto
from animus.core.intake.interfaces import SecondInstanceDecisionsRepository
from animus.core.intake.use_cases import GetSecondInstanceDecisionUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class GetSecondInstanceDecisionController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/second-instance-decision',
            status_code=200,
            response_model=SecondInstanceDecisionDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            second_instance_decisions_repository: Annotated[
                SecondInstanceDecisionsRepository,
                Depends(
                    DatabasePipe.get_second_instance_decisions_repository_from_request
                ),
            ],
        ) -> SecondInstanceDecisionDto:
            use_case = GetSecondInstanceDecisionUseCase(
                second_instance_decisions_repository=second_instance_decisions_repository,
            )

            return use_case.execute(analysis_id=analysis.id.value)
