from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.structures import Datetime, Id, Text


@entity
class Precedent(Entity):
    identifier: PrecedentIdentifier
    status: Text
    enunciation: Text
    thesis: Text
    last_updated_in_pangea_at: Datetime

    @classmethod
    def create(cls, dto: PrecedentDto) -> 'Precedent':
        return cls(
            id=Id.create(dto.id),
            identifier=PrecedentIdentifier.create(dto.identifier),
            status=Text.create(dto.status),
            enunciation=Text.create(dto.enunciation),
            thesis=Text.create(dto.thesis),
            last_updated_in_pangea_at=Datetime.create(dto.last_updated_in_pangea_at),
        )

    @property
    def dto(self) -> PrecedentDto:
        return PrecedentDto(
            id=self.id.value,
            identifier=self.identifier.dto,
            status=self.status.value,
            enunciation=self.enunciation.value,
            thesis=self.thesis.value,
            last_updated_in_pangea_at=self.last_updated_in_pangea_at.value.isoformat(),
        )
