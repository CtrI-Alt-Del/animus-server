from animus.core.intake.domain.errors.precedent_not_found_error import (
    PrecedentNotFoundError,
)
from animus.core.intake.domain.entities.dtos import PrecedentDto
from animus.core.intake.domain.structures.dtos import (
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.interfaces import PrecedentsRepository


class GetPrecedentUseCase:
    def __init__(
        self,
        precedents_repository: PrecedentsRepository,
    ) -> None:
        self._precedents_repository = precedents_repository

    def execute(
        self,
        precedent_identifier_dto: PrecedentIdentifierDto,
    ) -> PrecedentDto:
        precedent_identifier = PrecedentIdentifier.create(precedent_identifier_dto)
        precedent = self._precedents_repository.find_by_identifier(precedent_identifier)
        if precedent is None:
            raise PrecedentNotFoundError

        return precedent.dto
