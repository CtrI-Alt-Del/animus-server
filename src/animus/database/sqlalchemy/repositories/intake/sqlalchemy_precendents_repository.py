from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.errors.precedent_not_found_error import PrecedentNotFoundError
from animus.core.intake.domain.structures.court import Court
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.interfaces.precedents_repository import PrecedentsRepository
from animus.core.shared.domain.structures.integer import Integer
from animus.database.sqlalchemy.mappers.intake.precedents_mapper import PrecedentMapper
from animus.database.sqlalchemy.models.intake.precedent_model import PrecedentModel


class SqlalchemyPrecedentsRepository(PrecedentsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_id(self, court: Court, number: Integer) -> Precedent:
        model = self._sqlalchemy.scalar(
            select(PrecedentModel).where(
                PrecedentModel.court == court.dto, PrecedentModel.number == number.value
            )
        )
        if model is None:
            raise PrecedentNotFoundError

        return PrecedentMapper.to_entity(model)

    def add_many(self, precedents: list[Precedent]) -> None:
        self._sqlalchemy.add_all(
            [PrecedentMapper.to_model(precedent) for precedent in precedents]
        )

    def find_all_identifiers(self) -> set[PrecedentIdentifier]:
        results = self._sqlalchemy.execute(
            select(PrecedentModel.court, PrecedentModel.kind, PrecedentModel.number)
        ).all()

        identifiers:set[PrecedentIdentifier] = set()
        for row in results:
            dto = PrecedentIdentifierDto(
                court=row.court, kind=row.kind, number=row.number
            )
            identifiers.add(PrecedentIdentifier.create(dto))

        return identifiers
