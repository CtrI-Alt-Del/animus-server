from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.interfaces.summarize_petition_workflow import (
    SummarizePetitionWorkflow,
)
from animus.core.shared.domain.structures import Text
from animus.pipes.ai_pipe import AiPipe
from animus.pipes.storage_pipe import StoragePipe


class SummarizePetitionController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/petitions/{petition_id}/summary',
            status_code=201,
            response_model=PetitionSummaryDto,
        )
        def _(
            petition_id: str,
            document_content: Annotated[
                Text,
                Depends(StoragePipe.get_document_content),
            ],
            workflow: Annotated[
                SummarizePetitionWorkflow,
                Depends(AiPipe.get_summarize_petition_workflow),
            ],
        ) -> PetitionSummaryDto:
            return workflow.run(
                petition_id=petition_id,
                petition_document_content=document_content,
            )
