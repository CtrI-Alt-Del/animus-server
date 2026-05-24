from textwrap import dedent
from typing import TYPE_CHECKING, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs.intake.second_instance_judgment_draft_output import (
    SecondInstanceJudgmentDraftOutput,
)
from animus.ai.agno.squads import IntakeSquad
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.interfaces import GenerateSecondInstanceJudgmentDraftWorkflow
from animus.core.shared.domain.errors import AppError

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_JUDGMENT_DRAFT_INPUT: str = 'build-judgment-draft-input'
    GENERATE_JUDGMENT_DRAFT: str = 'generate-judgment-draft'


class AgnoGenerateSecondInstanceJudgmentDraftWorkflow(
    GenerateSecondInstanceJudgmentDraftWorkflow
):
    def __init__(self) -> None:
        self._squad = IntakeSquad()
        self._step_names = _StepNames()

    def run(
        self,
        analysis_id: str,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
    ) -> SecondInstanceJudgmentDraftDto:
        workflow = Workflow(
            name='generate-second-instance-judgment-draft',
            steps=[
                Step(
                    name=self._step_names.BUILD_JUDGMENT_DRAFT_INPUT,
                    executor=cast(
                        'StepExecutor',
                        self._build_judgment_draft_input_step,
                    ),
                ),
                Step(
                    name=self._step_names.GENERATE_JUDGMENT_DRAFT,
                    agent=self._squad.second_instance_judgment_draft_generator_agent,
                ),
            ],
            session_state={
                'analysis_id': analysis_id,
                'case_summary': case_summary,
                'precedents': precedents,
            },
        )

        output = workflow.run(input='start')
        return self._normalize_judgment_draft_output(output.content, analysis_id)

    def _build_judgment_draft_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessao', 'Session state is required')

        case_summary = run_context.session_state.get('case_summary')
        precedents = run_context.session_state.get('precedents')

        if not isinstance(case_summary, CaseSummary):
            msg = 'Case summary is required to build judgment draft input'
            raise AppError('Erro de execucao do workflow', msg)

        if not isinstance(precedents, list):
            msg = 'Analysis precedents are required to build judgment draft input'
            raise AppError('Erro de execucao do workflow', msg)

        precedents_candidates = cast('list[object]', precedents)
        if not all(
            isinstance(precedent, AnalysisPrecedent)
            for precedent in precedents_candidates
        ):
            msg = 'Analysis precedents are required to build judgment draft input'
            raise AppError('Erro de execucao do workflow', msg)

        precedents_list = cast('list[AnalysisPrecedent]', precedents_candidates)
        case_summary_dto = case_summary.dto

        applicable_precedents_count = sum(
            1 for precedent in precedents_list if precedent.applicability_level.dto == 2
        )
        no_applicable_precedent_notice = (
            'Aviso: não há precedente com applicability_level=2 nesta análise. '
            'Mantenha a minuta com fundamentação técnica e explicite distinções e aderências relevantes.'
            if applicable_precedents_count == 0
            else 'Sem aviso.'
        )

        precedents_input = '\n'.join(
            [
                dedent(
                    f"""
                    {index}. court: {precedent_dto.precedent.identifier.court}
                       kind: {precedent_dto.precedent.identifier.kind}
                       number: {precedent_dto.precedent.identifier.number}
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
            Elabore minuta de julgamento para segunda instância com base no caso e precedentes abaixo.
            Retorne saída estruturada com os campos:
            - report
            - merit_analysis
            - precedent_adherence_analysis
            - ruling
            - preliminary_issues (opcional)
            - no_applicable_precedent_notice (opcional)

            Resumo do caso:
            - case_summary: {case_summary_dto.case_summary}
            - legal_issue: {case_summary_dto.legal_issue}
            - central_question: {case_summary_dto.central_question}
            - type_of_action: {case_summary_dto.type_of_action}
            - relevant_laws: {', '.join(case_summary_dto.relevant_laws)}
            - key_facts: {', '.join(case_summary_dto.key_facts)}
            - requested_relief: {', '.join(case_summary_dto.triggered_relief)}
            - procedural_issues: {', '.join(case_summary_dto.procedural_issues)}
            - jurisdiction_issue: {case_summary_dto.jurisdiction_issue}
            - standing_issue: {case_summary_dto.standing_issue}

            Precedentes classificados:
            {precedents_input}

            {no_applicable_precedent_notice}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _normalize_judgment_draft_output(
        self,
        output: object,
        analysis_id: str,
    ) -> SecondInstanceJudgmentDraftDto:
        if not isinstance(output, SecondInstanceJudgmentDraftOutput):
            msg = 'Invalid output type from second instance judgment draft generator agent'
            raise AppError('Erro de execucao do workflow', msg)

        return SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report=output.report,
            merit_analysis=output.merit_analysis,
            precedent_adherence_analysis=output.precedent_adherence_analysis,
            ruling=output.ruling,
            preliminary_issues=output.preliminary_issues,
            no_applicable_precedent_notice=output.no_applicable_precedent_notice,
        )
