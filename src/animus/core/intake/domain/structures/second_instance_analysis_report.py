from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.second_instance_analysis_report_dto import (
    SecondInstanceAnalysisReportDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure


@structure
class SecondInstanceAnalysisReport(Structure):
    analysis: Analysis
    document: AnalysisDocument
    case_summary: CaseSummary
    precedents: list[AnalysisPrecedent]
    chosen_precedent: AnalysisPrecedent | None

    @classmethod
    def create(
        cls, dto: SecondInstanceAnalysisReportDto
    ) -> 'SecondInstanceAnalysisReport':
        return cls(
            analysis=Analysis.create(dto.analysis),
            document=AnalysisDocument.create(dto.document),
            case_summary=CaseSummary.create(dto.case_summary),
            precedents=[AnalysisPrecedent.create(item) for item in dto.precedents],
            chosen_precedent=(
                AnalysisPrecedent.create(dto.chosen_precedent)
                if dto.chosen_precedent is not None
                else None
            ),
        )

    @property
    def dto(self) -> SecondInstanceAnalysisReportDto:
        return SecondInstanceAnalysisReportDto(
            analysis=self.analysis.dto,
            document=self.document.dto,
            case_summary=self.case_summary.dto,
            precedents=[item.dto for item in self.precedents],
            chosen_precedent=(
                self.chosen_precedent.dto if self.chosen_precedent is not None else None
            ),
        )
