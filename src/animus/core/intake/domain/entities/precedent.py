from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.structures import Court, PrecedentKind, PrecedentStatus
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.structures import Datetime, Id, Integer, Text


@entity
class Precedent(Entity):
    court: Court
    number: Integer
    synthesis: Text
    kind: PrecedentKind
    status: PrecedentStatus
    title: Text
    enunciation: Text
    thesis: Text
    last_updated_in_pangea_at: Datetime

    @classmethod
    def create(cls, dto: PrecedentDto) -> 'Precedent':
        return cls(
            id=Id.create(dto.id),
            court=Court.create(dto.court),
            number=Integer.create(dto.number),
            synthesis=Text.create(dto.synthesis),
            kind=PrecedentKind.create(dto.kind),
            status=PrecedentStatus.create(dto.status),
            title=Text.create(dto.title),
            enunciation=Text.create(dto.enunciation),
            thesis=Text.create(dto.thesis),
            last_updated_in_pangea_at=Datetime.create(dto.last_updated_in_pangea_at),
        )

    @property
    def dto(self) -> PrecedentDto:
        return PrecedentDto(
            id=self.id.value,
            court=self.court.dto,
            number=self.number.value,
            synthesis=self.synthesis.value,
            kind=self.kind.dto,
            status=self.status.dto,
            title=self.title.value,
            enunciation=self.enunciation.value,
            thesis=self.thesis.value,
            last_updated_in_pangea_at=self.last_updated_in_pangea_at.value.isoformat(),
        )
