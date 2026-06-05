from animus.core.intake.domain.structures.dtos.second_instance_decision_dto import (
    SecondInstanceDecisionDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Text


@structure
class SecondInstanceDecision(Structure):
    analysis_id: Id
    description: Text

    @classmethod
    def create(cls, dto: SecondInstanceDecisionDto) -> 'SecondInstanceDecision':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            description=Text.create(dto.description),
        ).strip()

    def dto(self) -> SecondInstanceDecisionDto:
        return SecondInstanceDecisionDto(
            analysis_id=self.analysis_id.value,
            description=self.description.value,
        )

    def strip(self) -> 'SecondInstanceDecision':
        description = self.description.value.strip()
        if not description:
            raise ValidationError('Descricao da decisao obrigatoria')

        return self.__class__(
            analysis_id=self.analysis_id,
            description=Text.create(description),
        )
