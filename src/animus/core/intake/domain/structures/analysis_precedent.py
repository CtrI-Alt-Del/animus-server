from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Id, Logical, Percentage, Text


@structure
class AnalysisPrecedent(Structure):
    analysis_id: Id
    precedent: Precedent
    is_chosen: Logical
    applicability_percentage: Percentage | None
    synthesis: Text | None

    @classmethod
    def create(cls, dto: AnalysisPrecedentDto) -> 'AnalysisPrecedent':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            precedent=Precedent.create(dto.precedent),
            applicability_percentage=(
                Percentage.create(dto.applicability_percentage)
                if dto.applicability_percentage is not None
                else None
            ),
            is_chosen=Logical.create(dto.is_chosen),
            synthesis=Text.create(dto.synthesis) if dto.synthesis is not None else None,
        )

    @property
    def dto(self) -> AnalysisPrecedentDto:
        return AnalysisPrecedentDto(
            analysis_id=self.analysis_id.value,
            precedent=self.precedent.dto,
            synthesis=self.synthesis.value if self.synthesis is not None else None,
            applicability_percentage=(
                self.applicability_percentage.value
                if self.applicability_percentage is not None
                else None
            ),
            is_chosen=self.is_chosen.value,
        )
