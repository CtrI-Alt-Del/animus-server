from textwrap import dedent
from typing import TYPE_CHECKING, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs import CaseSummaryOutput
from animus.ai.agno.squads import IntakeSquad
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    SummarizeFirstInstanceCaseWorkflow,
)
from animus.core.intake.use_cases import CreateCaseSummaryUseCase
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Text

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_SUMMARIZATION_INPUT: str = 'build-summarization-input'
    SUMMARIZE_CASE: str = 'summarize-case'


class AgnoSummarizeSecondInstanceCaseWorkflow(SummarizeFirstInstanceCaseWorkflow):
    def __init__(
        self,
        case_summaries_repository: CaseSummariesRepository,
        analysis_documents_repository: AnalysisDocumentsRepository,
        analyses_repository: AnalysesRepository,
    ) -> None:
        self._create_case_summary_use_case = CreateCaseSummaryUseCase(
            case_summaries_repository=case_summaries_repository,
            analysis_documents_repository=analysis_documents_repository,
            analyses_repository=analyses_repository,
        )
        self._team = IntakeSquad()
        self._step_names = _StepNames()

    def run(self, analysis_id: str, document_content: Text) -> CaseSummaryDto:
        workflow = Workflow(
            name='summarize-second-instance-case',
            steps=[
                Step(
                    name=self._step_names.BUILD_SUMMARIZATION_INPUT,
                    executor=cast('StepExecutor', self._build_summarization_input_step),
                ),
                Step(
                    name=self._step_names.SUMMARIZE_CASE,
                    agent=self._team.second_instance_case_summarizer_agent,
                ),
            ],
            session_state={
                'document_content': document_content.value,
            },
        )

        output = workflow.run(input='start')
        summary_output = self._normalize_summary_output(output.content)

        return self._create_case_summary_use_case.execute(
            analysis_id=analysis_id,
            dto=summary_output,
        )

    def _build_summarization_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessao', 'Session state is required')

        document_content = str(run_context.session_state.get('document_content', ''))
        prompt = dedent(
            f"""
            Resuma o conteudo da petição inicial em contexto de segunda instancia.
            Entregue a saida estruturada contendo `case_summary`, `legal_issue`,
            `central_question`, `relevant_laws`, `key_facts` e `search_terms`.

            Diretrizes de segunda instancia:
            - destaque fundamentos e pedidos com foco recursal;
            - priorize `requested_relief`, `central_question`, `standing_issue` e
              `procedural_issues` no contexto de revisao da decisao;
            - identifique controversias estruturais que impactam admissibilidade,
              legitimidade e alcance do provimento pretendido.

            Conteudo da petição:
            {document_content}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _normalize_summary_output(self, output: object) -> CaseSummaryDto:
        if isinstance(output, CaseSummaryOutput):
            return CaseSummaryDto(
                case_summary=output.case_summary,
                legal_issue=output.legal_issue,
                central_question=output.central_question,
                relevant_laws=output.relevant_laws,
                key_facts=output.key_facts,
                search_terms=output.search_terms,
                type_of_action=output.type_of_action,
                secondary_legal_issues=output.secondary_legal_issues,
                alternative_questions=output.alternative_questions,
                jurisdiction_issue=output.jurisdiction_issue,
                standing_issue=output.standing_issue,
                requested_relief=output.triggered_relief,
                procedural_issues=output.procedural_issues,
                excluded_or_accessory_topics=output.excluded_or_accessory_topics,
            )

        msg = (
            'Invalid summary output type from second instance case summarizer workflow'
        )
        raise AppError('Erro de execucao do workflow', msg)
