from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.judge_analysis_report_dto import (
    JudgeAnalysisReportDto,
)
from animus.core.intake.domain.structures.judgment_draft import JudgmentDraft
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure


@structure
class JudgeAnalysisReport(Structure):
    analysis: Analysis
    document: AnalysisDocument
    case_summary: CaseSummary
    precedents: list[AnalysisPrecedent]
    judgment_draft: JudgmentDraft

    @classmethod
    def create(cls, dto: JudgeAnalysisReportDto) -> 'JudgeAnalysisReport':
        return cls(
            analysis=Analysis.create(dto.analysis),
            document=AnalysisDocument.create(dto.document),
            case_summary=CaseSummary.create(dto.case_summary),
            precedents=[AnalysisPrecedent.create(item) for item in dto.precedents],
            judgment_draft=JudgmentDraft.create(dto.judgment_draft),
        )

    @property
    def dto(self) -> JudgeAnalysisReportDto:
        return JudgeAnalysisReportDto(
            analysis=self.analysis.dto,
            document=self.document.dto,
            case_summary=self.case_summary.dto,
            precedents=[item.dto for item in self.precedents],
            judgment_draft=self.judgment_draft.dto,
        )
