from ctypes import Structure
from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.first_instance_analysis_report_dto import (
    FirstInstanceAnalysisReportDto,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.shared.domain.decorators import structure


@structure
class FirstInstanceAnalysisReport(Structure):
    analysis: Analysis
    document: AnalysisDocument
    case_summary: CaseSummary
    precedents: list[AnalysisPrecedent]
    judgment_draft: SecondInstanceJudgmentDraft

    @classmethod
    def create(
        cls, dto: FirstInstanceAnalysisReportDto
    ) -> 'FirstInstanceAnalysisReport':
        return cls(
            analysis=Analysis.create(dto.analysis),
            document=AnalysisDocument.create(dto.document),
            case_summary=CaseSummary.create(dto.case_summary),
            precedents=[AnalysisPrecedent.create(item) for item in dto.precedents],
            judgment_draft=SecondInstanceJudgmentDraft.create(dto.judgment_draft),
        )

    @property
    def dto(self) -> FirstInstanceAnalysisReportDto:
        return FirstInstanceAnalysisReportDto(
            analysis=self.analysis.dto,
            document=self.document.dto,
            case_summary=self.case_summary.dto,
            precedents=[item.dto for item in self.precedents],
            judgment_draft=self.judgment_draft.dto,
        )
