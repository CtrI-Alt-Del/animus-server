from textwrap import dedent
from typing import TYPE_CHECKING, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs.intake.petition_draft_output import PetitionDraftOutput
from animus.ai.agno.squads import IntakeSquad
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.interfaces import GeneratePetitionDraftWorkflow
from animus.core.shared.domain.errors import AppError

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_PETITION_DRAFT_INPUT: str = 'build-petition-draft-input'
    GENERATE_PETITION_DRAFT: str = 'generate-petition-draft'


class AgnoGeneratePetitionDraftWorkflow(GeneratePetitionDraftWorkflow):
    def __init__(self) -> None:
        self._squad = IntakeSquad()
        self._step_names = _StepNames()

    def run(
        self,
        analysis_id: str,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
    ) -> PetitionDraftDto:
        workflow = Workflow(
            name='generate-petition-draft',
            steps=[
                Step(
                    name=self._step_names.BUILD_PETITION_DRAFT_INPUT,
                    executor=cast(
                        'StepExecutor',
                        self._build_petition_draft_input_step,
                    ),
                ),
                Step(
                    name=self._step_names.GENERATE_PETITION_DRAFT,
                    agent=self._squad.petition_draft_generator_agent,
                ),
            ],
            session_state={
                'analysis_id': analysis_id,
                'case_summary': case_summary,
                'precedents': precedents,
            },
        )

        output = workflow.run(input='start')
        return self._normalize_petition_draft_output(output.content, analysis_id)

    def _build_petition_draft_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessao', 'Session state is required')

        case_summary = run_context.session_state.get('case_summary')
        precedents = run_context.session_state.get('precedents')

        if not isinstance(case_summary, CaseSummary):
            msg = 'Case summary is required to build petition draft input'
            raise AppError('Erro de execucao do workflow', msg)

        if not isinstance(precedents, list):
            msg = 'Analysis precedents are required to build petition draft input'
            raise AppError('Erro de execucao do workflow', msg)

        precedents_candidates = cast('list[object]', precedents)
        if not all(
            isinstance(precedent, AnalysisPrecedent)
            for precedent in precedents_candidates
        ):
            msg = 'Analysis precedents are required to build petition draft input'
            raise AppError('Erro de execucao do workflow', msg)

        precedents_list = cast('list[AnalysisPrecedent]', precedents_candidates)
        case_summary_dto = case_summary.dto

        precedents_input = '\n\n'.join(
            [
                dedent(
                    f"""
                    {index}. court: {precedent_dto.precedent.identifier.court}
                       kind: {precedent_dto.precedent.identifier.kind}
                       number: {precedent_dto.precedent.identifier.number}
                       status: {precedent_dto.precedent.status}
                       enunciation: {precedent_dto.precedent.enunciation}
                       thesis: {precedent_dto.precedent.thesis}
                       synthesis: {precedent_dto.synthesis}
                       applicability_level: {precedent_dto.applicability_level}
                    """
                ).strip()
                for index, precedent_dto in enumerate(
                    [precedent.dto for precedent in precedents_list],
                    start=1,
                )
            ]
        )

        prompt = dedent(
            f"""
            Elabore uma minuta estruturada de petição inicial com base no resumo do caso
            e nos precedentes já escolhidos abaixo.

            Retorne a saída estruturada com os campos:
            - structured_facts
            - legal_grounds
            - central_thesis
            - requests
            - precedent_citations

            Regras obrigatórias:
            - trate a minuta como sugestão técnica inicial para apoiar a análise do caso;
            - não afirme estratégia obrigatória, êxito garantido ou juízo definitivo sobre o mérito;
            - em `structured_facts`, organize os fatos de forma objetiva, cronológica e juridicamente relevante;
            - em `legal_grounds`, desenvolva os fundamentos jurídicos com aderência ao resumo e aos precedentes fornecidos;
            - em `central_thesis`, sintetize a tese principal que sustenta a petição;
            - em `requests`, liste pedidos juridicamente formuláveis em frases curtas;
            - em `precedent_citations`, cada item deve citar explicitamente tribunal, tipo e número,
              além da tese ou trecho útil ao caso concreto.

            Resumo estruturado do caso:
            - case_summary: {case_summary_dto.case_summary}
            - legal_issue: {case_summary_dto.legal_issue}
            - central_question: {case_summary_dto.central_question}
            - type_of_action: {case_summary_dto.type_of_action}
            - relevant_laws: {', '.join(case_summary_dto.relevant_laws)}
            - key_facts: {', '.join(case_summary_dto.key_facts)}
            - requested_relief: {', '.join(case_summary_dto.requested_relief)}
            - procedural_issues: {', '.join(case_summary_dto.procedural_issues)}
            - secondary_legal_issues: {', '.join(case_summary_dto.secondary_legal_issues)}
            - alternative_questions: {', '.join(case_summary_dto.alternative_questions)}
            - jurisdiction_issue: {case_summary_dto.jurisdiction_issue}
            - standing_issue: {case_summary_dto.standing_issue}
            - excluded_or_accessory_topics: {', '.join(case_summary_dto.excluded_or_accessory_topics)}

            Precedentes escolhidos:
            {precedents_input}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _normalize_petition_draft_output(
        self,
        output: object,
        analysis_id: str,
    ) -> PetitionDraftDto:
        if isinstance(output, dict):
            output = PetitionDraftOutput.model_validate(output)

        if not isinstance(output, PetitionDraftOutput):
            msg = 'Invalid output type from petition draft generator agent'
            raise AppError('Erro de execucao do workflow', msg)

        return PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts=output.structured_facts,
            legal_grounds=output.legal_grounds,
            central_thesis=output.central_thesis,
            requests=output.requests,
            precedent_citations=output.precedent_citations,
        )
