import json
from collections.abc import Mapping
from textwrap import dedent
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow
from pydantic import BaseModel

from animus.ai.agno.outputs import CaseSummaryOutput, PetitionSummaryOutput
from animus.ai.agno.squads import IntakeSquad
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    SummarizeCaseAssessmentCaseWorkflow,
)
from animus.core.intake.use_cases import CreateCaseSummaryUseCase
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Text

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_SUMMARIZATION_INPUT: str = 'build-summarization-input'
    SUMMARIZE_CASE: str = 'summarize-case'


class AgnoSummarizeCaseAssessmentCaseWorkflow(SummarizeCaseAssessmentCaseWorkflow):
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
            name='summarize-case-assessment-case',
            steps=[
                Step(
                    name=self._step_names.BUILD_SUMMARIZATION_INPUT,
                    executor=cast(
                        'StepExecutor',
                        self._build_case_assessment_summary_input_step,
                    ),
                ),
                Step(
                    name=self._step_names.SUMMARIZE_CASE,
                    agent=self._team.case_assessment_case_summarizer_agent,
                ),
            ],
            session_state={
                'document_content': document_content.value,
            },
        )

        output = workflow.run(input='start')
        summary_output = self._normalize_case_assessment_summary_output(output.content)

        return self._create_case_summary_use_case.execute(
            analysis_id=analysis_id,
            dto=summary_output,
        )

    def _build_case_assessment_summary_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessao', 'Session state is required')

        document_content = str(run_context.session_state.get('document_content', ''))
        prompt = dedent(
            f"""
            Resuma o documento jurídico abaixo para uma análise de viabilidade de petição inicial.
            Entregue a saída estruturada contendo `case_summary`, `legal_issue`,
            `central_question`, `relevant_laws`, `key_facts`, `search_terms`,
            `type_of_action`, `secondary_legal_issues`, `alternative_questions`,
            `jurisdiction_issue`, `standing_issue`, `requested_relief`,
            `procedural_issues` e `excluded_or_accessory_topics`.

            Diretrizes específicas para case assessment:
            - priorize os fatos juridicamente relevantes para avaliar a pretensão inicial;
            - destaque pedidos potencialmente formuláveis sem assumir que são definitivos;
            - identifique controvérsias estruturais que impactem competência,
              legitimidade, cabimento ou necessidade de prova;
            - produza termos de busca úteis para localizar precedentes aplicáveis ao caso.
            - seja conciso para evitar truncamento: `case_summary` com no máximo 120 palavras;
            - `legal_issue` e `central_question` devem ter uma frase cada;
            - cada item de listas deve ser curto, específico e sem justificativas extensas.

            Conteúdo do documento:
            {document_content}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _normalize_case_assessment_summary_output(
        self,
        output: object,
    ) -> CaseSummaryDto:
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
        unwrapped_output = self._unwrap_output_content(output)

        if isinstance(unwrapped_output, CaseSummaryOutput):
            return unwrapped_output

        if isinstance(unwrapped_output, PetitionSummaryOutput):
            return CaseSummaryOutput.model_validate(unwrapped_output.model_dump())

        if isinstance(unwrapped_output, BaseModel):
            return CaseSummaryOutput.model_validate(unwrapped_output.model_dump())

        if isinstance(unwrapped_output, str):
            stripped_output = unwrapped_output.strip()
            if stripped_output.startswith(('{', '[')):
                return CaseSummaryOutput.model_validate_json(stripped_output)

            msg = self._build_invalid_output_message(stripped_output)
            raise AppError('Erro de execucao do workflow', msg)

        if isinstance(unwrapped_output, Mapping):
            data = cast(
                'dict[str, Any]',
                dict(cast('Mapping[str, object]', unwrapped_output)),
            )
            return CaseSummaryOutput.model_validate(data)

        msg = 'Invalid summary output type from case assessment summarizer workflow'
        raise AppError('Erro de execucao do workflow', msg)

    def _build_invalid_output_message(self, output: str) -> str:
        compact_output = ' '.join(output.split())
        snippet = compact_output[:240]
        return f'Case assessment summarizer agent returned non-JSON content: {snippet}'

    def _unwrap_output_content(self, output_content: object) -> object:
        unwrapped_content: object = output_content
        for _ in range(6):
            if isinstance(
                unwrapped_content,
                (CaseSummaryOutput, PetitionSummaryOutput, BaseModel, Mapping),
            ):
                return cast('object', unwrapped_content)

            if isinstance(unwrapped_content, str):
                try:
                    unwrapped_content = json.loads(unwrapped_content)
                    continue
                except json.JSONDecodeError:
                    return unwrapped_content

            nested_content = getattr(unwrapped_content, 'content', None)
            if nested_content is None or nested_content is unwrapped_content:
                return unwrapped_content

            unwrapped_content = nested_content

        return unwrapped_content
