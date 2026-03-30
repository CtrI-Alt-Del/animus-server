from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.domain.structures.dtos.analysis_petition_dto import (
    AnalysisPetitionDto,
)
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class AnalysisPetition(Structure):
    petition: Petition
    summary: PetitionSummary | None

    @classmethod
    def create(cls, dto: AnalysisPetitionDto) -> 'AnalysisPetition':
        return cls(
            petition=Petition.create(dto.petition),
            summary=(
                PetitionSummary.create(dto.summary) if dto.summary is not None else None
            ),
        )

    @property
    def dto(self) -> AnalysisPetitionDto:
        return AnalysisPetitionDto(
            petition=self.petition.dto,
            summary=self.summary.dto if self.summary is not None else None,
        )
