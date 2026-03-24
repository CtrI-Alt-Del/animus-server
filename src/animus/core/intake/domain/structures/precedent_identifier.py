from ctypes import Structure
from animus.core.intake.domain.structures import Court, PrecedentKind
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Integer


@structure
class PrecedentIdentifier(Structure):
    court: Court
    kind: PrecedentKind
    number: Integer

    @classmethod
    def create(cls, dto: PrecedentIdentifierDto) -> 'PrecedentIdentifier':
        return cls(
            court=Court.create(dto.court),
            kind=PrecedentKind.create(dto.kind),
            number=Integer.create(dto.number),
        )

    @property
    def dto(self) -> PrecedentIdentifierDto:
        return PrecedentIdentifierDto(
            court=self.court.dto,
            kind=self.kind.dto,
            number=self.number.value,
        )
