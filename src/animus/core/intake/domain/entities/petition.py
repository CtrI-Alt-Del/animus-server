from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.domain.structures.petition_document import PetitionDocument
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.structures import Datetime, Id


@entity
class Petition(Entity):
    analysis_id: Id
    uploaded_at: Datetime
    document: PetitionDocument

    @classmethod
    def create(cls, dto: PetitionDto) -> 'Petition':
        return cls(
            id=Id.create(dto.id),
            analysis_id=Id.create(dto.analysis_id),
            uploaded_at=Datetime.create(dto.uploaded_at),
            document=PetitionDocument.create(dto.document),
        )

    @property
    def dto(self) -> PetitionDto:
        return PetitionDto(
            id=self.id.value,
            analysis_id=self.analysis_id.value,
            uploaded_at=self.uploaded_at.value.isoformat(),
            document=self.document.dto,
        )
