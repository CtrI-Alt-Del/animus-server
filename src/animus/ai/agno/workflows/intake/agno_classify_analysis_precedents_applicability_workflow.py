import json
from collections.abc import Mapping
from textwrap import dedent
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs.intake.analysis_precedents_applicability_classification_output import (
    AnalysisPrecedentsApplicabilityClassificationOutput,
)
from animus.ai.agno.teams import IntakeSquad
from animus.core.intake.domain.errors import PetitionSummaryUnavailableError
from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_row_dto import (
    AnalysisPrecedentDatasetRowDto as AnalysisPrecedentDatasetRowDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.interfaces.classify_analysis_precedents_applicability_workflow import (
    ClassifyAnalysisPrecedentsApplicabilityWorkflow,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.use_cases.create_analysis_precedent_applicability_feedback_use_case import (
    CreateAnalysisPrecedentApplicabilityFeedbackUseCase,
)
from animus.core.intake.use_cases.create_analysis_precedent_dataset_row_use_case import (
    CreateAnalysisPrecedentDatasetRowUseCase,
)
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Id

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_CLASSIFICATION_INPUT: str = 'build-classification-input'
    CLASSIFY_PRECEDENTS_APPLICABILITY: str = 'classify-precedents-applicability'
    CREATE_CLASSIFICATIONS: str = 'create-classifications'


def build_classification_prompt(
    petition_summary_dto: PetitionSummaryDto,
    precedents_input: list[str],
) -> str:
    return dedent(
        f"""
        Classifique a aplicabilidade dos precedentes candidatos para a petição abaixo.
        Retorne todos os itens no formato estruturado esperado com
        `precedent_id`, `applicability_level` e `confidence`.

        ## Petição

        - case_summary: {petition_summary_dto.case_summary}
        - legal_issue: {petition_summary_dto.legal_issue}
        - central_question: {petition_summary_dto.central_question}
        - relevant_laws: {', '.join(petition_summary_dto.relevant_laws)}
        - key_facts: {', '.join(petition_summary_dto.key_facts)}
        - search_terms: {', '.join(petition_summary_dto.search_terms)}

        ## Precedentes candidatos

        Os precedentes estão ordenados por similarity_score decrescente —
        os primeiros têm maior similaridade semântica com a petição.
        Precedentes no final da lista com similarity_score baixo tendem a
        ser label 0, mas avalie sempre thesis e enunciation antes de decidir.

        {chr(10).join(precedents_input)}
        """
    ).strip()


class AgnoClassifyAnalysisPrecedentsApplicabilityWorkflow(
    ClassifyAnalysisPrecedentsApplicabilityWorkflow
):
    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
        create_analysis_precedent_applicability_feedback_use_case: CreateAnalysisPrecedentApplicabilityFeedbackUseCase,
        create_analysis_precedent_dataset_row_use_case: CreateAnalysisPrecedentDatasetRowUseCase,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository
        self._create_analysis_precedent_applicability_feedback_use_case = (
            create_analysis_precedent_applicability_feedback_use_case
        )
        self._create_analysis_precedent_dataset_row_use_case = (
            create_analysis_precedent_dataset_row_use_case
        )
        self._team = IntakeSquad()
        self._step_names = _StepNames()

    def run(
        self,
        analysis_id: str,
        analysis_precedents: list[AnalysisPrecedentDto],
    ) -> list[AnalysisPrecedentDatasetRowDto]:
        if not analysis_precedents:
            return []

        workflow = Workflow(
            name='classify-analysis-precedents-applicability',
            steps=[
                Step(
                    name=self._step_names.BUILD_CLASSIFICATION_INPUT,
                    executor=cast(
                        'StepExecutor', self._build_classification_input_step
                    ),
                ),
                Step(
                    name=self._step_names.CLASSIFY_PRECEDENTS_APPLICABILITY,
                    agent=(
                        self._team.analysis_precedents_applicability_classifier_agent
                    ),
                ),
                Step(
                    name=self._step_names.CREATE_CLASSIFICATIONS,
                    executor=cast('StepExecutor', self._create_classifications_step),
                    max_retries=0,
                ),
            ],
            session_state={
                'analysis_id': analysis_id,
                'analysis_precedents': analysis_precedents,
            },
        )

        output = workflow.run(input='start')
        return self._normalize_dataset_rows_output(output.content)

    def _normalize_dataset_rows_output(
        self,
        output_content: object,
    ) -> list[AnalysisPrecedentDatasetRowDto]:
        unwrapped_content = self._unwrap_output_content(output_content)

        if not isinstance(unwrapped_content, list):
            msg = 'Invalid classifications output type from workflow'
            raise AppError('Erro de execução do workflow', msg)

        return [
            self._coerce_dataset_row(dataset_row_candidate)
            for dataset_row_candidate in cast('list[object]', unwrapped_content)
        ]

    def _unwrap_output_content(self, output_content: object) -> object:
        unwrapped_content: object = output_content
        for _ in range(6):
            if isinstance(unwrapped_content, list):
                return cast('object', unwrapped_content)

            if isinstance(unwrapped_content, str):
                try:
                    unwrapped_content = json.loads(unwrapped_content)
                    continue
                except json.JSONDecodeError:
                    return unwrapped_content

            if isinstance(unwrapped_content, Mapping):
                mapped_content = cast('Mapping[str, object]', unwrapped_content)
                nested_content = mapped_content.get('content')
                if nested_content is None:
                    return cast('object', unwrapped_content)

                unwrapped_content = nested_content
                continue

            nested_content = getattr(unwrapped_content, 'content', None)
            if nested_content is None or nested_content is unwrapped_content:
                return unwrapped_content

            unwrapped_content = nested_content

        return unwrapped_content

    def _coerce_dataset_row(
        self,
        dataset_row_candidate: object,
    ) -> AnalysisPrecedentDatasetRowDto:
        if isinstance(dataset_row_candidate, AnalysisPrecedentDatasetRowDto):
            return dataset_row_candidate

        if isinstance(dataset_row_candidate, Mapping):
            dataset_row_data = cast(
                'dict[str, Any]',
                dict(cast('Mapping[str, object]', dataset_row_candidate)),
            )
            return AnalysisPrecedentDatasetRowDto(**dataset_row_data)

        msg = 'Invalid classifications output type from workflow'
        raise AppError('Erro de execução do workflow', msg)

    def _build_classification_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessão', 'Session state is required')

        analysis_id = str(run_context.session_state.get('analysis_id', ''))
        raw_analysis_precedents = run_context.session_state.get('analysis_precedents')

        if not analysis_id:
            msg = 'Analysis id is required to classify precedents applicability'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(raw_analysis_precedents, list):
            msg = (
                'Analysis precedents are required to classify precedents applicability'
            )
            raise AppError('Erro de execução do workflow', msg)

        analysis_precedents_candidates = cast('list[object]', raw_analysis_precedents)
        if not all(
            isinstance(analysis_precedent, AnalysisPrecedentDto)
            for analysis_precedent in analysis_precedents_candidates
        ):
            msg = (
                'Analysis precedents are required to classify precedents applicability'
            )
            raise AppError('Erro de execução do workflow', msg)

        analysis_precedents = cast(
            'list[AnalysisPrecedentDto]',
            analysis_precedents_candidates,
        )
        petition_summary = self._petition_summaries_repository.find_by_analysis_id(
            analysis_id=Id.create(analysis_id),
        )
        if petition_summary is None:
            raise PetitionSummaryUnavailableError

        petition_summary_dto = petition_summary.dto
        analysis_precedents_by_precedent_id: dict[str, AnalysisPrecedentDto] = {}
        precedents_input: list[str] = []

        for index, analysis_precedent in enumerate(analysis_precedents, start=1):
            precedent_id = analysis_precedent.precedent.id
            if precedent_id is None:
                msg = 'Precedent id is required to classify precedents applicability'
                raise AppError('Erro de execução do workflow', msg)

            analysis_precedents_by_precedent_id[precedent_id] = analysis_precedent
            precedents_input.append(
                dedent(
                    f"""
                    {index}. precedent_id: {precedent_id}
                    court: {analysis_precedent.precedent.identifier.court}
                    kind: {analysis_precedent.precedent.identifier.kind}
                    number: {analysis_precedent.precedent.identifier.number}
                    status: {analysis_precedent.precedent.status}
                    similarity_score: {analysis_precedent.similarity_score}
                    thesis_similarity_score: {analysis_precedent.thesis_similarity_score}
                    enunciation_similarity_score: {analysis_precedent.enunciation_similarity_score}
                    total_search_hits: {analysis_precedent.total_search_hits}
                    similarity_rank: {analysis_precedent.similarity_rank}
                    legal_features:
                        central_issue_match: {analysis_precedent.legal_features.central_issue_match if analysis_precedent.legal_features is not None else 0}
                        structural_issue_match: {analysis_precedent.legal_features.structural_issue_match if analysis_precedent.legal_features is not None else 0}
                        context_compatibility: {analysis_precedent.legal_features.context_compatibility if analysis_precedent.legal_features is not None else 0}
                        is_lateral_topic: {analysis_precedent.legal_features.is_lateral_topic if analysis_precedent.legal_features is not None else 0}
                        is_accessory_topic: {analysis_precedent.legal_features.is_accessory_topic if analysis_precedent.legal_features is not None else 0}
                    enunciation: {analysis_precedent.precedent.enunciation}
                    thesis: {analysis_precedent.precedent.thesis}
                    synthesis: {analysis_precedent.synthesis}
                    """
                ).strip()
            )

        run_context.session_state['analysis_precedents_by_precedent_id'] = (
            analysis_precedents_by_precedent_id
        )

        prompt = build_classification_prompt(
            petition_summary_dto=petition_summary_dto,
            precedents_input=precedents_input,
        )

        return StepOutput(content=prompt)

    def _create_classifications_step(
        self,
        step_input: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessão', 'Session state is required')

        analysis_id = self._get_analysis_id(run_context)
        raw_classification_output = step_input.get_last_step_content()
        classification_output = self._coerce_classification_output(
            raw_classification_output
        )
        analysis_precedents_by_precedent_id = (
            self._get_analysis_precedents_by_precedent_id(run_context)
        )

        dataset_rows: list[AnalysisPrecedentDatasetRowDto] = []
        processed_precedent_ids: set[str] = set()
        for classification in classification_output.items:
            if classification.confidence.strip().lower() not in (
                'high',
                'medium',
                'low',
            ):
                continue

            precedent_id = classification.precedent_id
            if precedent_id in processed_precedent_ids:
                continue

            analysis_precedent = analysis_precedents_by_precedent_id.get(precedent_id)
            if analysis_precedent is None:
                continue

            feedback = (
                self._create_analysis_precedent_applicability_feedback_use_case.execute(
                    analysis_id=analysis_id,
                    precedent_id=precedent_id,
                    applicability_level=classification.applicability_level,
                )
            )
            dataset_row = self._create_analysis_precedent_dataset_row_use_case.execute(
                analysis_precedent=analysis_precedent,
                feedback=feedback,
            )
            dataset_rows.append(dataset_row)
            processed_precedent_ids.add(precedent_id)

        return StepOutput(content=dataset_rows)

    def _get_analysis_id(self, run_context: RunContext) -> str:
        session_state = run_context.session_state
        if session_state is None:
            raise AppError('Erro de sessão', 'Session state is required')

        raw_analysis_id = session_state.get('analysis_id', '')
        analysis_id = str(raw_analysis_id)
        if not analysis_id:
            msg = 'Analysis id is required to create classifications'
            raise AppError('Erro de execução do workflow', msg)

        return analysis_id

    def _coerce_classification_output(
        self,
        raw_classification_output: object,
    ) -> AnalysisPrecedentsApplicabilityClassificationOutput:
        if isinstance(
            raw_classification_output,
            AnalysisPrecedentsApplicabilityClassificationOutput,
        ):
            return raw_classification_output

        msg = 'Invalid classifications output type from classifier agent'
        raise AppError('Erro de execução do workflow', msg)

    def _get_analysis_precedents_by_precedent_id(
        self,
        run_context: RunContext,
    ) -> dict[str, AnalysisPrecedentDto]:
        session_state = run_context.session_state
        if session_state is None:
            raise AppError('Erro de sessão', 'Session state is required')

        raw_analysis_precedents_by_precedent_id = session_state.get(
            'analysis_precedents_by_precedent_id'
        )
        if not isinstance(raw_analysis_precedents_by_precedent_id, dict):
            msg = 'Analysis precedents are required to create classifications'
            raise AppError('Erro de execução do workflow', msg)

        analysis_precedents_by_precedent_id_candidates = cast(
            'dict[object, object]',
            raw_analysis_precedents_by_precedent_id,
        )
        analysis_precedents_by_precedent_id: dict[str, AnalysisPrecedentDto] = {}

        for (
            precedent_id_candidate,
            analysis_precedent_candidate,
        ) in analysis_precedents_by_precedent_id_candidates.items():
            if not isinstance(precedent_id_candidate, str) or not isinstance(
                analysis_precedent_candidate,
                AnalysisPrecedentDto,
            ):
                msg = 'Analysis precedents are required to create classifications'
                raise AppError('Erro de execução do workflow', msg)

            analysis_precedents_by_precedent_id[precedent_id_candidate] = (
                analysis_precedent_candidate
            )

        return analysis_precedents_by_precedent_id
