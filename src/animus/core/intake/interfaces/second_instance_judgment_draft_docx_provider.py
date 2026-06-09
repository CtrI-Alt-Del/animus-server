from typing import Protocol

from animus.core.intake.domain.structures import (
    AnalysisPrecedent,
    SecondInstanceDecision,
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)


class SecondInstanceJudgmentDraftDocxProvider(Protocol):
    def export(
        self,
        analysis_id: str,
        analysis_name: str,
        judgment_draft: SecondInstanceJudgmentDraft,
        second_instance_decision: SecondInstanceDecision,
        precedents: list[AnalysisPrecedent],
    ) -> AnalysisDocumentDto: ...
