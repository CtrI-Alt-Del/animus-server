from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.intake.use_cases.create_petition_use_case import CreatePetitionUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class _DocumentBody(BaseModel):
    file_path: str
    name: str

    def to_dto(self) -> PetitionDocumentDto:
        return PetitionDocumentDto(file_path=self.file_path, name=self.name)


class _Body(BaseModel):
    analysis_id: str
    uploaded_at: str
    document: _DocumentBody


class CreatePetitionController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/petitions', status_code=201, response_model=PetitionDto)
        def _(
            body: _Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            petitions_repository: Annotated[
                PetitionsRepository,
                Depends(DatabasePipe.get_petitions_repository_from_request),
            ],
        ) -> PetitionDto:
            IntakePipe.verify_analysis_by_account(
                analysis_id=body.analysis_id,
                account_id=account_id,
                analisyses_repository=analisyses_repository,
            )

            use_case = CreatePetitionUseCase(petitions_repository=petitions_repository)

            return use_case.execute(
                analysis_id=body.analysis_id,
                uploaded_at=body.uploaded_at,
                document=body.document.to_dto(),
            )
