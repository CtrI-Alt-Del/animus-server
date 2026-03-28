from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.dtos import AnalysisPrecedentDto
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Id, Logical, Percentage


@structure
class AnalysisPrecedent(Structure):
    analysis_id: Id
    precedent: Precedent
    applicability_percentage: Percentage | None
    is_chosen: Logical

    @classmethod
    def create(cls, dto: AnalysisPrecedentDto) -> 'AnalysisPrecedent':
        applicability_percentage = (
            Percentage.create(dto.applicability_percentage)
            if dto.applicability_percentage is not None
            else None
        )

        return cls(
            analysis_id=Id.create(dto.analysis_id),
            precedent=Precedent.create(dto.precedent),
            applicability_percentage=applicability_percentage,
            is_chosen=Logical.create(dto.is_chosen),
        )

    @property
    def dto(self) -> AnalysisPrecedentDto:
        return AnalysisPrecedentDto(
            analysis_id=self.analysis_id.value,
            precedent=self.precedent.dto,
            applicability_percentage=(
                self.applicability_percentage.value
                if self.applicability_percentage is not None
                else None
            ),
            is_chosen=self.is_chosen.value,
        )
