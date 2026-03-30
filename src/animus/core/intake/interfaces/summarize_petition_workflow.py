from typing import Protocol

from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.structures import Text


class SummarizePetitionWorkflow(Protocol):
    def run(
        self,
        petition_id: str,
        petition_document_content: Text,
    ) -> PetitionSummaryDto: ...
