from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.database.sqlalchemy.models.intake.precedent_model import PrecedentModel


class PrecedentMapper:
    @staticmethod
    def to_entity(model: PrecedentModel) -> Precedent:
        return Precedent.create(
            PrecedentDto(
                id=model.id,
                identifier=PrecedentIdentifierDto(
                    court=model.court,
                    kind=model.kind,
                    number=model.number,
                ),
                status=model.status,
                enunciation=model.enunciation,
                thesis=model.thesis,
                last_updated_in_pangea_at=model.last_updated_in_pangea_at.isoformat(),
            )
        )

    @staticmethod
    def to_model(entity: Precedent) -> PrecedentModel:
        return PrecedentModel(
            id=entity.id.value,
            court=entity.identifier.court.dto,
            kind=entity.identifier.kind.dto,
            number=entity.identifier.number.value,
            status=entity.status.dto,
            enunciation=entity.enunciation.value,
            thesis=entity.thesis.value,
            last_updated_in_pangea_at=entity.last_updated_in_pangea_at.value,
        )
