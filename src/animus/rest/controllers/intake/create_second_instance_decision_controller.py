from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos import SecondInstanceDecisionDto
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceDecisionsRepository,
)
from animus.core.intake.use_cases import CreateSecondInstanceDecisionUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class _Body(BaseModel):
    description: str = Field(..., min_length=1)

    @field_validator('description')
    @classmethod
    def validate_description(cls, value: str) -> str:
        normalized_value = value.strip()
        if normalized_value == '':
            raise ValueError('Description must not be blank')
        return normalized_value


class CreateSecondInstanceDecisionController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/second-instance-decision',
            status_code=201,
            response_model=SecondInstanceDecisionDto,
        )
        def _(
            body: _Body,
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
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
        ) -> SecondInstanceDecisionDto:
            use_case = CreateSecondInstanceDecisionUseCase(
                second_instance_decisions_repository=second_instance_decisions_repository,
                analyses_repository=analyses_repository,
            )

            return use_case.execute(
                analysis_id=analysis.id.value,
                description=body.description,
            )
