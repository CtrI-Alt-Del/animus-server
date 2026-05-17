from animus.core.intake.domain.structures.dtos.extracted_petition_dto import (
    ExtractedPetitionDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Integer


@structure
class ExtractedPetition(Structure):
    analysis_id: Id
    first_page: Integer
    last_page: Integer

    @classmethod
    def create(cls, dto: ExtractedPetitionDto) -> 'ExtractedPetition':
        if dto.first_page < 1:
            raise ValidationError(
                'Primeira pagina da petição deve ser maior ou igual a 1'
            )

        if dto.last_page < dto.first_page:
            raise ValidationError(
                'Ultima pagina da petição deve ser maior ou igual a primeira pagina'
            )

        return cls(
            analysis_id=Id.create(dto.analysis_id),
            first_page=Integer.create(dto.first_page),
            last_page=Integer.create(dto.last_page),
        )

    @property
    def dto(self) -> ExtractedPetitionDto:
        return ExtractedPetitionDto(
            analysis_id=self.analysis_id.value,
            first_page=self.first_page.value,
            last_page=self.last_page.value,
        )
