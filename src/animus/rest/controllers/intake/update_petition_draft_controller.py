from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos import PetitionDraftDto
from animus.core.intake.interfaces import AnalysesRepository, PetitionDraftsRepository
from animus.core.intake.use_cases import UpdatePetitionDraftUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class _Body(BaseModel):
    structured_facts: str = Field(..., min_length=1)
    legal_grounds: str = Field(..., min_length=1)
    central_thesis: str = Field(..., min_length=1)
    requests: list[str]
    precedent_citations: list[str]

    @field_validator('structured_facts', 'legal_grounds', 'central_thesis')
    @classmethod
    def validate_non_blank_string(cls, value: str) -> str:
        if value.strip() == '':
            raise ValueError('Field must not be blank')
        return value

    @field_validator('requests', 'precedent_citations')
    @classmethod
    def validate_non_empty_list(cls, value: list[str]) -> list[str]:
        if len(value) == 0:
            raise ValueError('List must not be empty')

        for item in value:
            if item.strip() == '':
                raise ValueError('List items must not be blank')

        return value

    def to_dto(self, analysis_id: str) -> PetitionDraftDto:
        return PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts=self.structured_facts,
            legal_grounds=self.legal_grounds,
            central_thesis=self.central_thesis,
            requests=self.requests,
            precedent_citations=self.precedent_citations,
        )


class UpdatePetitionDraftController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.put(
            '/analyses/{analysis_id}/petition-drafts',
            status_code=200,
            response_model=PetitionDraftDto,
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
            petition_drafts_repository: Annotated[
                PetitionDraftsRepository,
                Depends(DatabasePipe.get_petition_drafts_repository_from_request),
            ],
        ) -> PetitionDraftDto:
            use_case = UpdatePetitionDraftUseCase(
                analyses_repository=analyses_repository,
                petition_drafts_repository=petition_drafts_repository,
            )

            return use_case.execute(
                analysis_id=analysis.id.value,
                dto=body.to_dto(analysis.id.value),
            )
