import json
from collections.abc import Mapping
from textwrap import dedent
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow
from pydantic import BaseModel

from animus.ai.agno.outputs.intake.petition_draft_output import PetitionDraftOutput
from animus.ai.agno.squads import IntakeSquad
from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.intake.interfaces import RegeneratePetitionDraftWorkflow
from animus.core.shared.domain.errors import AppError

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_PETITION_DRAFT_REGENERATION_INPUT: str = (
        'build-petition-draft-regeneration-input'
    )
    REGENERATE_PETITION_DRAFT: str = 'regenerate-petition-draft'


class AgnoRegeneratePetitionDraftWorkflow(RegeneratePetitionDraftWorkflow):
    def __init__(self) -> None:
        self._squad = IntakeSquad()
        self._step_names = _StepNames()

    def run(
        self,
        analysis_id: str,
        current_draft: PetitionDraft,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
        comments: str,
    ) -> PetitionDraftDto:
        workflow = Workflow(
            name='regenerate-petition-draft',
            steps=[
                Step(
                    name=self._step_names.BUILD_PETITION_DRAFT_REGENERATION_INPUT,
                    executor=cast(
                        'StepExecutor',
                        self._build_petition_draft_regeneration_input_step,
                    ),
                ),
                Step(
                    name=self._step_names.REGENERATE_PETITION_DRAFT,
                    agent=self._squad.petition_draft_reviser_agent,
                ),
            ],
            session_state={
                'analysis_id': analysis_id,
                'current_draft': current_draft,
                'case_summary': case_summary,
                'precedents': precedents,
                'comments': comments,
            },
        )

        output = workflow.run(input='start')
        return self._normalize_petition_draft_output(output.content, analysis_id)

    def _build_petition_draft_regeneration_input_step(
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

        if not isinstance(current_draft, PetitionDraft):
            msg = 'Current petition draft is required to build regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(case_summary, CaseSummary):
            msg = 'Case summary is required to build petition draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(precedents, list):
            msg = 'Analysis precedents are required to build petition draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        precedents_candidates = cast('list[object]', precedents)
        if not all(
            isinstance(precedent, AnalysisPrecedent)
            for precedent in precedents_candidates
        ):
            msg = 'Analysis precedents are required to build petition draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(comments, str):
            msg = 'Comments are required to build petition draft regeneration input'
            raise AppError('Erro de execução do workflow', msg)

        precedents_list = cast('list[AnalysisPrecedent]', precedents_candidates)
        case_summary_dto = case_summary.dto
        current_draft_dto = current_draft.dto

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
            Revise a minuta estruturada de petição inicial abaixo com base no resumo do caso,
            nos precedentes escolhidos e nos comentários do usuário.

            Retorne a saída estruturada com os campos:
            - structured_facts
            - legal_grounds
            - central_thesis
            - requests
            - precedent_citations

            Regras obrigatórias:
            - preserve tudo o que não foi solicitado para alterar;
            - mantenha coerência integral com o resumo do caso e com os precedentes fornecidos;
            - não invente fatos, fundamentos, pedidos ou precedentes novos;
            - trate a minuta revisada como sugestão técnica inicial, sem afirmar estratégia obrigatória
              nem resultado garantido;
            - ajuste apenas o necessário para refletir os comentários do usuário.

            Comentários do usuário:
            {comments}

            Minuta atual:
            - structured_facts: {current_draft_dto.structured_facts}
            - legal_grounds: {current_draft_dto.legal_grounds}
            - central_thesis: {current_draft_dto.central_thesis}
            - requests: {', '.join(current_draft_dto.requests)}
            - precedent_citations: {', '.join(current_draft_dto.precedent_citations)}

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
        normalized_output = self._coerce_petition_draft_output(output)

        return PetitionDraftDto(
            analysis_id=analysis_id,
            structured_facts=self._normalize_text(normalized_output.structured_facts),
            legal_grounds=self._normalize_text(normalized_output.legal_grounds),
            central_thesis=self._normalize_text(normalized_output.central_thesis),
            requests=self._normalize_text_list(normalized_output.requests),
            precedent_citations=self._normalize_text_list(
                normalized_output.precedent_citations,
            ),
        )

    def _normalize_text(self, value: str) -> str:
        return value.replace('\\r\\n', '\n').replace('\\n', '\n').strip()

    def _normalize_text_list(self, items: list[str]) -> list[str]:
        return [self._normalize_text(item) for item in items]

    def _coerce_petition_draft_output(self, output: object) -> PetitionDraftOutput:
        unwrapped_output = self._unwrap_output_content(output)

        if isinstance(unwrapped_output, PetitionDraftOutput):
            return unwrapped_output

        if isinstance(unwrapped_output, BaseModel):
            return PetitionDraftOutput.model_validate(unwrapped_output.model_dump())

        if isinstance(unwrapped_output, str):
            stripped_output = unwrapped_output.strip()
            if stripped_output.startswith(('{', '[')):
                return PetitionDraftOutput.model_validate_json(stripped_output)

            msg = self._build_invalid_output_message(stripped_output)
            raise AppError('Erro de execução do workflow', msg)

        if isinstance(unwrapped_output, Mapping):
            data = cast(
                'dict[str, Any]',
                dict(cast('Mapping[str, object]', unwrapped_output)),
            )
            return PetitionDraftOutput.model_validate(data)

        msg = 'Invalid output type from petition draft reviser agent'
        raise AppError('Erro de execução do workflow', msg)

    def _build_invalid_output_message(self, output: str) -> str:
        compact_output = ' '.join(output.split())
        snippet = compact_output[:240]
        return f'Petition draft reviser agent returned non-JSON content: {snippet}'

    def _unwrap_output_content(self, output_content: object) -> object:
        unwrapped_content: object = output_content
        for _ in range(6):
            if isinstance(unwrapped_content, (PetitionDraftOutput, BaseModel, Mapping)):
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
