from textwrap import dedent
from typing import TYPE_CHECKING, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs import CaseSummaryOutput, PetitionSummaryOutput
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


class AgnoSummarizeFirstInstanceCaseWorkflow(SummarizeFirstInstanceCaseWorkflow):
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
            name='summarize-case',
            steps=[
                Step(
                    name=self._step_names.BUILD_SUMMARIZATION_INPUT,
                    executor=cast('StepExecutor', self._build_summarization_input_step),
                ),
                Step(
                    name=self._step_names.SUMMARIZE_CASE,
                    agent=self._team.first_instance_case_summarizer_agent,
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
            Resuma o documento juridico a seguir em portugues brasileiro.
            Entregue a saida estruturada contendo `case_summary`, `legal_issue`,
            `central_question`, `relevant_laws`, `key_facts` e `search_terms`.

            Conteudo do documento:
            {document_content}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _normalize_summary_output(self, output: object) -> CaseSummaryDto:
        normalized_output = self._coerce_summary_output(output)

        return CaseSummaryDto(
            case_summary=normalized_output.case_summary,
            legal_issue=normalized_output.legal_issue,
            central_question=normalized_output.central_question,
            relevant_laws=normalized_output.relevant_laws,
            key_facts=normalized_output.key_facts,
            search_terms=normalized_output.search_terms,
            type_of_action=normalized_output.type_of_action,
            secondary_legal_issues=normalized_output.secondary_legal_issues,
            alternative_questions=normalized_output.alternative_questions,
            jurisdiction_issue=normalized_output.jurisdiction_issue,
            standing_issue=normalized_output.standing_issue,
            requested_relief=normalized_output.requested_relief,
            procedural_issues=normalized_output.procedural_issues,
            excluded_or_accessory_topics=normalized_output.excluded_or_accessory_topics,
        )

    def _coerce_summary_output(self, output: object) -> CaseSummaryOutput:
        if isinstance(output, CaseSummaryOutput):
            return output

        if isinstance(output, PetitionSummaryOutput):
            return CaseSummaryOutput.model_validate(output.model_dump())

        if isinstance(output, dict):
            return CaseSummaryOutput.model_validate(output)

        msg = 'Invalid summary output type from case summarizer workflow'
        raise AppError('Erro de execucao do workflow', msg)
