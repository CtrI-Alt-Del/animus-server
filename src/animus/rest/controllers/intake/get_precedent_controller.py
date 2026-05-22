from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities.dtos import PrecedentDto
from animus.core.intake.domain.structures.dtos import (
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces import PrecedentsRepository
from animus.core.intake.use_cases import GetPrecedentUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class GetPrecedentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/precedents',
            status_code=200,
            response_model=PrecedentDto,
        )
        def _(
            court: str,
            kind: str,
            number: int,
            _account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            precedents_repository: Annotated[
                PrecedentsRepository,
                Depends(DatabasePipe.get_precedents_repository_from_request),
            ],
        ) -> PrecedentDto:
            use_case = GetPrecedentUseCase(
                precedents_repository=precedents_repository,
            )

            return use_case.execute(
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court=court,
                    kind=kind,
                    number=number,
                ),
            )
