from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.structures.dtos import PetitionDraftDto
from animus.core.intake.interfaces import AnalysesRepository, PetitionDraftsRepository
from animus.core.intake.use_cases import GetPetitionDraftUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class GetPetitionDraftController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/petition-drafts',
            status_code=200,
            response_model=PetitionDraftDto,
        )
        def _(
            analysis_id: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            petition_drafts_repository: Annotated[
                PetitionDraftsRepository,
                Depends(DatabasePipe.get_petition_drafts_repository_from_request),
            ],
        ) -> PetitionDraftDto:
            use_case = GetPetitionDraftUseCase(
                analyses_repository=analyses_repository,
                petition_drafts_repository=petition_drafts_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id.value,
            )
