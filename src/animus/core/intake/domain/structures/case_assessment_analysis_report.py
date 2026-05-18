from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.case_assessment_analysis_report_dto import (
    CaseAssessmentAnalysisReportDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure


@structure
class CaseAssessmentAnalysisReport(Structure):
    analysis: Analysis
    document: AnalysisDocument
    case_summary: CaseSummary
    precedents: list[AnalysisPrecedent]
    petition_draft: PetitionDraft

    @classmethod
    def create(
        cls, dto: CaseAssessmentAnalysisReportDto
    ) -> 'CaseAssessmentAnalysisReport':
        return cls(
            analysis=Analysis.create(dto.analysis),
            document=AnalysisDocument.create(dto.document),
            case_summary=CaseSummary.create(dto.case_summary),
            precedents=[AnalysisPrecedent.create(item) for item in dto.precedents],
            petition_draft=PetitionDraft.create(dto.petition_draft),
        )

    @property
    def dto(self) -> CaseAssessmentAnalysisReportDto:
        return CaseAssessmentAnalysisReportDto(
            analysis=self.analysis.dto,
            document=self.document.dto,
            case_summary=self.case_summary.dto,
            precedents=[item.dto for item in self.precedents],
            petition_draft=self.petition_draft.dto,
        )
