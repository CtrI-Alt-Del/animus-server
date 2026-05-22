from typing import Protocol

from animus.core.intake.domain.structures.dtos.case_summary_dto import (
    CaseSummaryDto,
)
from animus.core.shared.domain.structures import Text


class SummarizePetitionWorkflow(Protocol):
    def run(
        self,
        petition_id: str,
        petition_document_content: Text,
    ) -> CaseSummaryDto: ...
