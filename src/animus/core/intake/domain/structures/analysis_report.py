from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos.analysis_report_dto import (
    AnalysisReportDto,
)
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure


@structure
class AnalysisReport(Structure):
    analysis: Analysis
    petition: Petition
    summary: PetitionSummary
    precedents: list[AnalysisPrecedent]
    chosen_precedent: AnalysisPrecedent | None

    @classmethod
    def create(cls, dto: AnalysisReportDto) -> 'AnalysisReport':
        return cls(
            analysis=Analysis.create(dto.analysis),
            petition=Petition.create(dto.petition),
            summary=PetitionSummary.create(dto.summary),
            precedents=[AnalysisPrecedent.create(item) for item in dto.precedents],
            chosen_precedent=(
                AnalysisPrecedent.create(dto.chosen_precedent)
                if dto.chosen_precedent is not None
                else None
            ),
        )

    @property
    def dto(self) -> AnalysisReportDto:
        return AnalysisReportDto(
            analysis=self.analysis.dto,
            petition=self.petition.dto,
            summary=self.summary.dto,
            precedents=[item.dto for item in self.precedents],
            chosen_precedent=(
                self.chosen_precedent.dto if self.chosen_precedent is not None else None
            ),
        )
