from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.interfaces.precedents_repository import PrecedentsRepository
from animus.core.shared.responses import ListResponse
from animus.core.shared.responses.page_pagination_response import PagePaginationResponse
from animus.database.sqlalchemy.mappers.intake.precedents_mapper import PrecedentMapper
from animus.database.sqlalchemy.models.intake.precedent_model import PrecedentModel


class SqlalchemyPrecedentsRepository(PrecedentsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_identifier(self, identifier: PrecedentIdentifier) -> Precedent | None:
        model = self._sqlalchemy.scalar(
            select(PrecedentModel).where(
                PrecedentModel.court == identifier.court.dto,
                PrecedentModel.kind == identifier.kind.dto,
                PrecedentModel.number == identifier.number.value,
            )
        )
        if model is None:
            return None

        return PrecedentMapper.to_entity(model)

    def find_many_by_identifiers(
        self,
        identifiers: list[PrecedentIdentifier],
    ) -> ListResponse[Precedent]:
        if not identifiers:
            return ListResponse(items=[])

        models = self._sqlalchemy.scalars(
            select(PrecedentModel).where(
                tuple_(
                    PrecedentModel.court,
                    PrecedentModel.kind,
                    PrecedentModel.number,
                ).in_(
                    [
                        (
                            identifier.court.dto,
                            identifier.kind.dto,
                            identifier.number.value,
                        )
                        for identifier in identifiers
                    ]
                )
            )
        ).all()

        return ListResponse(
            items=[PrecedentMapper.to_entity(model) for model in models]
        )

    def add_many(self, precedents: list[Precedent]) -> None:
        self._sqlalchemy.add_all(
            [PrecedentMapper.to_model(precedent) for precedent in precedents]
        )

    def find_all_identifiers(self) -> set[PrecedentIdentifier]:
        results = self._sqlalchemy.execute(
            select(PrecedentModel.court, PrecedentModel.kind, PrecedentModel.number)
        ).all()

        identifiers: set[PrecedentIdentifier] = set()
        for row in results:
            dto = PrecedentIdentifierDto(
                court=row.court, kind=row.kind, number=row.number
            )
            identifiers.add(PrecedentIdentifier.create(dto))

        return identifiers

    def find_page(self, page: int, page_size: int) -> PagePaginationResponse[Precedent]:
        offset = (page - 1) * page_size
        total = self._sqlalchemy.scalar(
            select(func.count()).select_from(PrecedentModel)
        )

        models = self._sqlalchemy.scalars(
            select(PrecedentModel)
            .order_by(
                PrecedentModel.court.asc(),
                PrecedentModel.kind.asc(),
                PrecedentModel.number.asc(),
            )
            .offset(offset)
            .limit(page_size)
        ).all()

        return PagePaginationResponse[Precedent](
            items=[PrecedentMapper.to_entity(model) for model in models],
            total=total or 0,
            page=page,
            page_size=page_size,
        )
