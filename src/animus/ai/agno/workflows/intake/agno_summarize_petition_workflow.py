from textwrap import dedent
from typing import TYPE_CHECKING, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs import PetitionSummaryOutput
from animus.ai.agno.teams import IntakeTeam
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.summarize_petition_workflow import (
    SummarizePetitionWorkflow,
)
from animus.core.intake.use_cases import CreatePetitionSummaryUseCase
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Text

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_SUMMARIZATION_INPUT: str = "build-summarization-input"
    SUMMARIZE_PETITION: str = "summarize-petition"


class AgnoSummarizePetitionWorkflow(SummarizePetitionWorkflow):
    def __init__(
        self, petition_summaries_repository: PetitionSummariesRepository
    ) -> None:
        self._create_petition_summary_use_case = CreatePetitionSummaryUseCase(
            petition_summaries_repository=petition_summaries_repository,
        )
        self._team = IntakeTeam()
        self._step_names = _StepNames()

    def run(
        self,
        petition_id: str,
        petition_document_content: Text,
    ) -> PetitionSummaryDto:
        workflow = Workflow(
            name="summarize-petition",
            steps=[
                Step(
                    name=self._step_names.BUILD_SUMMARIZATION_INPUT,
                    executor=cast("StepExecutor", self._build_summarization_input_step),
                ),
                Step(
                    name=self._step_names.SUMMARIZE_PETITION,
                    agent=self._team.petition_summarizer_agent,
                ),
            ],
            session_state={
                "petition_document_content": petition_document_content.value,
            },
        )

        output = workflow.run(input="start")
        summary_output = self._normalize_summary_output(output.content)

        return self._create_petition_summary_use_case.execute(
            petition_id=petition_id,
            dto=summary_output,
        )

    def _build_summarization_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError("Erro de sessão", "Session state is required")

        petition_document_content = str(
            run_context.session_state.get("petition_document_content", "")
        )
        prompt = dedent(
            f"""
            Resuma a petição a seguir em português brasileiro.
            Entregue a saída estruturada contendo `case_summary`, `legal_issue`,
            `central_question`, `relevant_laws`, `key_facts` e `search_terms`.

            Conteúdo da petição:
            {petition_document_content}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _normalize_summary_output(self, output: object) -> PetitionSummaryDto:
        if isinstance(output, PetitionSummaryOutput):
            return PetitionSummaryDto(
                case_summary=output.case_summary,
                legal_issue=output.legal_issue,
                central_question=output.central_question,
                relevant_laws=output.relevant_laws,
                key_facts=output.key_facts,
                search_terms=output.search_terms,
            )

        msg = "Invalid summary output type from petition summarizer workflow"
        raise AppError("Erro de execução do workflow", msg)
