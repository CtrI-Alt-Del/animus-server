from typing import Annotated

from fastapi import Depends

from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.analysis_documents_repository import (
    AnalysisDocumentsRepository,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.case_summaries_repository import (
    CaseSummariesRepository,
)
from animus.core.intake.interfaces.generate_judgment_draft_workflow import (
    GenerateSecondInstanceJudgmentDraftWorkflow,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.summarize_case_workflow import (
    SummarizeFirstInstanceCaseWorkflow,
)
from animus.core.intake.interfaces.synthesize_analysis_precedents_workflow import (
    SynthesizeAnalysisPrecedentsWorkflow,
)
from animus.pipes.database_pipe import DatabasePipe


class AiPipe:
    @staticmethod
    def get_summarize_case_workflow(
        case_summaries_repository: Annotated[
            CaseSummariesRepository,
            Depends(DatabasePipe.get_case_summaries_repository_from_request),
        ],
        analysis_documents_repository: Annotated[
            AnalysisDocumentsRepository,
            Depends(DatabasePipe.get_analysis_documents_repository_from_request),
        ],
        analisyses_repository: Annotated[
            AnalisysesRepository,
            Depends(DatabasePipe.get_analisyses_repository_from_request),
        ],
    ) -> SummarizeFirstInstanceCaseWorkflow:
        from animus.ai.agno.workflows.intake.agno_summarize_first_instance_case_workflow import (
            AgnoSummarizeFirstInstanceCaseWorkflow,
        )

        return AgnoSummarizeFirstInstanceCaseWorkflow(
            case_summaries_repository=case_summaries_repository,
            analysis_documents_repository=analysis_documents_repository,
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

    @staticmethod
    def get_generate_judgment_draft_workflow() -> (
        GenerateSecondInstanceJudgmentDraftWorkflow
    ):
        from animus.ai.agno.workflows.intake.agno_generate_second_instance_judgment_draft_workflow import (
            AgnoGenerateSecondInstanceJudgmentDraftWorkflow,
        )

        return AgnoGenerateSecondInstanceJudgmentDraftWorkflow()
