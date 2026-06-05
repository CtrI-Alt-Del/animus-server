from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import UpdateSecondInstanceJudgmentDraftUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class _Body(BaseModel):
    report: str = Field(..., min_length=1)
    merit_analysis: str = Field(..., min_length=1)
    precedent_adherence_analysis: str = Field(..., min_length=1)
    ruling: list[str]
    preliminary_issues: str | None = None
    no_applicable_precedent_notice: str | None = None

    @field_validator(
        'report',
        'merit_analysis',
        'precedent_adherence_analysis',
    )
    @classmethod
    def validate_non_blank_string(cls, value: str) -> str:
        normalized_value = value.strip()
        if normalized_value == '':
            raise ValueError('Field must not be blank')
        return normalized_value

    @field_validator('ruling')
    @classmethod
    def validate_ruling(cls, value: list[str]) -> list[str]:
        if len(value) == 0:
            raise ValueError('List must not be empty')

        normalized_items = [item.strip() for item in value]
        if any(item == '' for item in normalized_items):
            raise ValueError('List items must not be blank')

        return normalized_items

    def to_dto(self, analysis_id: str) -> SecondInstanceJudgmentDraftDto:
        return SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report=self.report,
            merit_analysis=self.merit_analysis,
            precedent_adherence_analysis=self.precedent_adherence_analysis,
            ruling=self.ruling,
            preliminary_issues=self.preliminary_issues,
            no_applicable_precedent_notice=self.no_applicable_precedent_notice,
        )


class UpdateSecondInstanceJudgmentDraftController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.put(
            '/analyses/{analysis_id}/second-instance-judgment-drafts',
            status_code=200,
            response_model=SecondInstanceJudgmentDraftDto,
        )
        def _(
            body: _Body,
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            judgment_drafts_repository: Annotated[
                SecondInstanceJudgmentDraftsRepository,
                Depends(DatabasePipe.get_judgment_drafts_repository_from_request),
            ],
        ) -> SecondInstanceJudgmentDraftDto:
            use_case = UpdateSecondInstanceJudgmentDraftUseCase(
                analyses_repository=analyses_repository,
                judgment_drafts_repository=judgment_drafts_repository,
            )

            return use_case.execute(
                analysis_id=analysis.id.value,
                dto=body.to_dto(analysis.id.value),
            )
