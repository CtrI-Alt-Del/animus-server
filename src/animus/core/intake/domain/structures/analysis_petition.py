from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.analysis_petition_dto import (
    AnalysisPetitionDto,
)
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class AnalysisPetition(Structure):
    document: AnalysisDocument
    case_summary: CaseSummary | None

    @classmethod
    def create(cls, dto: AnalysisPetitionDto) -> 'AnalysisPetition':
        return cls(
            document=AnalysisDocument.create(dto.document),
            case_summary=(
                CaseSummary.create(dto.case_summary)
                if dto.case_summary is not None
                else None
            ),
        )

    @property
    def dto(self) -> AnalysisPetitionDto:
        return AnalysisPetitionDto(
            document=self.document.dto,
            case_summary=(
                self.case_summary.dto if self.case_summary is not None else None
            ),
        )
