import json
from collections.abc import Mapping
from textwrap import dedent
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow
from pydantic import BaseModel

from animus.ai.agno.outputs.intake.second_instance_judgment_draft_output import (
    SecondInstanceJudgmentDraftOutput,
)
from animus.ai.agno.squads import IntakeSquad
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_decision import (
    SecondInstanceDecision,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.interfaces import RegenerateSecondInstanceJudgmentDraftWorkflow
from animus.core.shared.domain.errors import AppError

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_JUDGMENT_DRAFT_REGENERATION_INPUT: str = (
        'build-judgment-draft-regeneration-input'
    )
    REGENERATE_JUDGMENT_DRAFT: str = 'regenerate-judgment-draft'


class AgnoRegenerateSecondInstanceJudgmentDraftWorkflow(
    RegenerateSecondInstanceJudgmentDraftWorkflow
):
    def __init__(self) -> None:
        self._squad = IntakeSquad()
        self._step_names = _StepNames()

    def run(
        self,
        analysis_id: str,
        current_draft: SecondInstanceJudgmentDraft,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
        comments: str,
        second_instance_decision: SecondInstanceDecision,
    ) -> SecondInstanceJudgmentDraftDto:
        workflow = Workflow(
            name='regenerate-second-instance-judgment-draft',
            steps=[
                Step(
                    name=self._step_names.BUILD_JUDGMENT_DRAFT_REGENERATION_INPUT,
                    executor=cast(
                        'StepExecutor',
                        self._build_judgment_draft_regeneration_input_step,
                    ),
                ),
                Step(
                    name=self._step_names.REGENERATE_JUDGMENT_DRAFT,
                    agent=self._squad.second_instance_judgment_draft_reviser_agent,
                ),
            ],
            session_state={
                'analysis_id': analysis_id,
                'current_draft': current_draft,
                'case_summary': case_summary,
                'precedents': precedents,
                'comments': comments,
                'second_instance_decision': second_instance_decision,
            },
        )

        output = workflow.run(input='start')
        return self._normalize_judgment_draft_output(output.content, analysis_id)

    def _build_judgment_draft_regeneration_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessao', 'Session state is required')

        current_draft = run_context.session_state.get('current_draft')
        case_summary = run_context.session_state.get('case_summary')
        precedents = run_context.session_state.get('precedents')
        comments = run_context.session_state.get('comments')
        second_instance_decision = run_context.session_state.get(
            'second_instance_decision'
        )

        if not isinstance(current_draft, SecondInstanceJudgmentDraft):
            msg = 'Current judgment draft is required to build regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(case_summary, CaseSummary):
            msg = 'Case summary is required to build judgment draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(precedents, list):
            msg = 'Analysis precedents are required to build judgment draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        precedents_candidates = cast('list[object]', precedents)
        if not all(
            isinstance(precedent, AnalysisPrecedent)
            for precedent in precedents_candidates
        ):
            msg = 'Analysis precedents are required to build judgment draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(comments, str):
            msg = 'Comments are required to build judgment draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(second_instance_decision, SecondInstanceDecision):
            msg = (
                'Second instance decision is required to build judgment draft '
                'regeneration input'
            )
            raise AppError('Erro de execução do workflow', msg)

        precedents_list = cast('list[AnalysisPrecedent]', precedents_candidates)
        current_draft_dto = current_draft.dto
        case_summary_dto = case_summary.dto

        applicable_precedents_count = sum(
            1 for precedent in precedents_list if precedent.applicability_level.dto == 2
        )
        no_applicable_precedent_notice = (
            'Aviso: não há precedente com applicability_level=2 nesta análise. '
            'Mantenha a revisão tecnicamente fundamentada e explicite distinções e aderências relevantes.'
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

        excluded_topics = case_summary_dto.excluded_or_accessory_topics or []
        excluded_topics_text = (
            ', '.join(excluded_topics) if excluded_topics else 'nenhum'
        )
        preliminary_issues = current_draft_dto.preliminary_issues or 'nenhuma'
        no_precedent_notice = (
            current_draft_dto.no_applicable_precedent_notice or 'nenhum'
        )

        prompt = dedent(
            f"""
            Revise a minuta estruturada de acórdão abaixo com base no resumo do caso,
            nos precedentes escolhidos e nos comentários do usuário.

            Retorne a saída estruturada com os campos:
            - report
            - merit_analysis
            - precedent_adherence_analysis
            - ruling
            - preliminary_issues (opcional)
            - no_applicable_precedent_notice (opcional)

            Regras obrigatórias:
            - preserve tudo o que não foi solicitado para alterar;
            - mantenha coerência integral com o resumo do caso e com os precedentes fornecidos;
            - não invente fatos, fundamentos, dispositivo ou precedentes novos;
            - ajuste apenas o necessário para refletir os comentários do usuário com coerência técnica.

            Comentários do usuário:
            {comments}

            Minuta atual:
            - report: {current_draft_dto.report}
            - merit_analysis: {current_draft_dto.merit_analysis}
            - precedent_adherence_analysis: {current_draft_dto.precedent_adherence_analysis}
            - ruling: {', '.join(current_draft_dto.ruling)}
            - preliminary_issues: {preliminary_issues}
            - no_applicable_precedent_notice: {no_precedent_notice}

            Resumo do caso:
            - case_summary: {case_summary_dto.case_summary}
            - legal_issue: {case_summary_dto.legal_issue}
            - central_question: {case_summary_dto.central_question}
            - type_of_action: {case_summary_dto.type_of_action}
            - relevant_laws: {', '.join(case_summary_dto.relevant_laws)}
            - key_facts: {', '.join(case_summary_dto.key_facts)}
            - requested_relief: {', '.join(case_summary_dto.requested_relief)}
            - procedural_issues: {', '.join(case_summary_dto.procedural_issues)}
            - jurisdiction_issue: {case_summary_dto.jurisdiction_issue}
            - standing_issue: {case_summary_dto.standing_issue}
            - excluded_or_accessory_topics: {excluded_topics_text}

            Decisão pretendida pelo julgador:
            - second_instance_decision: {second_instance_decision.description.value}

            Precedentes escolhidos:
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
        normalized_output = self._coerce_judgment_draft_output(output)

        return SecondInstanceJudgmentDraftDto(
            analysis_id=analysis_id,
            report=normalized_output.report,
            merit_analysis=normalized_output.merit_analysis,
            precedent_adherence_analysis=normalized_output.precedent_adherence_analysis,
            ruling=normalized_output.ruling,
            preliminary_issues=normalized_output.preliminary_issues,
            no_applicable_precedent_notice=(
                normalized_output.no_applicable_precedent_notice
            ),
        )

    def _coerce_judgment_draft_output(
        self,
        output: object,
    ) -> SecondInstanceJudgmentDraftOutput:
        unwrapped_output = self._unwrap_output_content(output)

        if isinstance(unwrapped_output, SecondInstanceJudgmentDraftOutput):
            return unwrapped_output

        if isinstance(unwrapped_output, BaseModel):
            return SecondInstanceJudgmentDraftOutput.model_validate(
                unwrapped_output.model_dump()
            )

        if isinstance(unwrapped_output, str):
            stripped_output = unwrapped_output.strip()
            if stripped_output.startswith(('{', '[')):
                return SecondInstanceJudgmentDraftOutput.model_validate_json(
                    stripped_output
                )

            msg = self._build_invalid_output_message(stripped_output)
            raise AppError('Erro de execução do workflow', msg)

        if isinstance(unwrapped_output, Mapping):
            data = cast(
                'dict[str, Any]',
                dict(cast('Mapping[str, object]', unwrapped_output)),
            )
            return SecondInstanceJudgmentDraftOutput.model_validate(data)

        msg = 'Invalid output type from second instance judgment draft reviser agent'
        raise AppError('Erro de execução do workflow', msg)

    def _build_invalid_output_message(self, output: str) -> str:
        compact_output = ' '.join(output.split())
        snippet = compact_output[:240]
        return (
            'Second instance judgment draft reviser agent returned non-JSON '
            f'content: {snippet}'
        )

    def _unwrap_output_content(self, output_content: object) -> object:
        unwrapped_content: object = output_content
        for _ in range(6):
            if isinstance(
                unwrapped_content,
                (SecondInstanceJudgmentDraftOutput, BaseModel, Mapping),
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
