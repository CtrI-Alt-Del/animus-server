from typing import Annotated

from fastapi import Depends

from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.intake.interfaces.summarize_petition_workflow import (
    SummarizePetitionWorkflow,
)
from animus.core.intake.interfaces.synthesize_analysis_precedents_workflow import (
    SynthesizeAnalysisPrecedentsWorkflow,
)
from animus.pipes.database_pipe import DatabasePipe


class AiPipe:
    @staticmethod
    def get_summarize_petition_workflow(
        petition_summaries_repository: Annotated[
            PetitionSummariesRepository,
            Depends(DatabasePipe.get_petition_summaries_repository_from_request),
        ],
        petitions_repository: Annotated[
            PetitionsRepository,
            Depends(DatabasePipe.get_petitions_repository_from_request),
        ],
        analisyses_repository: Annotated[
            AnalisysesRepository,
            Depends(DatabasePipe.get_analisyses_repository_from_request),
        ],
    ) -> SummarizePetitionWorkflow:
        from animus.ai.agno.workflows.intake.agno_summarize_petition_workflow import (
            AgnoSummarizePetitionWorkflow,
        )

        return AgnoSummarizePetitionWorkflow(
            petition_summaries_repository=petition_summaries_repository,
            petitions_repository=petitions_repository,
            analisyses_repository=analisyses_repository,
        )

    @staticmethod
    def get_synthesize_analysis_precedents_workflow(
        petition_summaries_repository: PetitionSummariesRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        analisyses_repository: AnalisysesRepository,
    ) -> SynthesizeAnalysisPrecedentsWorkflow:
        from animus.ai.agno.workflows.intake.agno_synthesize_analysis_precedents_workflow import (
            AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow,
        )

        return AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow(
            petition_summaries_repository=petition_summaries_repository,
            analysis_precedents_repository=analysis_precedents_repository,
            analisyses_repository=analisyses_repository,
        )
