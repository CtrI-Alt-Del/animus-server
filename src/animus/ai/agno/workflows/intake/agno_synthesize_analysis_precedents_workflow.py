from textwrap import dedent
from typing import TYPE_CHECKING, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.teams import IntakeSquad
from animus.core.intake.domain.errors import (
    PetitionSummaryUnavailableError,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.synthesize_analysis_precedents_workflow import (
    SynthesizeAnalysisPrecedentsWorkflow,
)
from animus.core.intake.use_cases import CreateAnalysisPrecedentsUseCase
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Id

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    FETCH_PETITION_SUMMARY: str = 'fetch-petition-summary'
    BUILD_SYNTHESIS_INPUT: str = 'build-synthesis-input'
    SYNTHESIZE_ANALYSIS_PRECEDENTS: str = 'synthesize-analysis-precedents'
    PERSIST_ANALYSIS_PRECEDENTS: str = 'persist-analysis-precedents'


class AgnoSynthesizeAnalysisPrecedentsWorkflow(SynthesizeAnalysisPrecedentsWorkflow):
    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        analisyses_repository: AnalisysesRepository,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository
        self._create_analysis_precedents_use_case = CreateAnalysisPrecedentsUseCase(
            analysis_precedents_repository=analysis_precedents_repository,
            analisyses_repository=analisyses_repository,
        )
        self._team = IntakeSquad()
        self._step_names = _StepNames()

    def run(
        self,
        analysis_id: str,
        filters_dto: AnalysisPrecedentsSearchFiltersDto,
        analysis_precedents: list[AnalysisPrecedentDto],
    ) -> None:
        if not analysis_precedents:
            return

        workflow = Workflow(
            name='synthesize-analysis-precedents',
            steps=[
                Step(
                    name=self._step_names.FETCH_PETITION_SUMMARY,
                    executor=cast('StepExecutor', self._fetch_petition_summary_step),
                ),
                Step(
                    name=self._step_names.BUILD_SYNTHESIS_INPUT,
                    executor=cast('StepExecutor', self._build_synthesis_input_step),
                ),
                Step(
                    name=self._step_names.SYNTHESIZE_ANALYSIS_PRECEDENTS,
                    agent=self._team.analysis_precedents_synthesizer_agent,
                ),
                Step(
                    name=self._step_names.PERSIST_ANALYSIS_PRECEDENTS,
                    executor=cast(
                        'StepExecutor', self._persist_analysis_precedents_step
                    ),
                ),
            ],
            session_state={
                'analysis_id': analysis_id,
                'filters_dto': filters_dto,
                'analysis_precedents': analysis_precedents,
            },
        )

        workflow.run(input='start')

    def _fetch_petition_summary_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessão', 'Session state is required')

        analysis_id = str(run_context.session_state.get('analysis_id', ''))
        if not analysis_id:
            msg = 'Analysis id is required to synthesize analysis precedents'
            raise AppError('Erro de execução do workflow', msg)

        petition_summary = self._petition_summaries_repository.find_by_analysis_id(
            analysis_id=Id.create(analysis_id),
        )
        if petition_summary is None:
            raise PetitionSummaryUnavailableError

        run_context.session_state['petition_summary'] = petition_summary

        return StepOutput(content='petition-summary-loaded')

    def _build_synthesis_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessão', 'Session state is required')

        petition_summary = run_context.session_state.get('petition_summary')
        analysis_precedents = run_context.session_state.get('analysis_precedents')

        if petition_summary is None:
            msg = 'Petition summary is required to build precedents synthesis input'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(analysis_precedents, list):
            msg = 'Analysis precedents are required to build precedents synthesis input'
            raise AppError('Erro de execução do workflow', msg)

        analysis_precedents_dto = cast(
            'list[AnalysisPrecedentDto]', analysis_precedents
        )

        petition_summary_dto = petition_summary.dto
        precedents_input = '\n'.join(
            [
                dedent(
                    f"""
                    {index}. court: {analysis_precedent.precedent.identifier.court}
                       kind: {analysis_precedent.precedent.identifier.kind}
                       number: {analysis_precedent.precedent.identifier.number}
                       similarity_percentage: {analysis_precedent.similarity_percentage}
                       status: {analysis_precedent.precedent.status}
                       enunciation: {analysis_precedent.precedent.enunciation}
                       thesis: {analysis_precedent.precedent.thesis}
                    """
                ).strip()
                for index, analysis_precedent in enumerate(
                    analysis_precedents_dto,
                    start=1,
                )
            ]
        )

        prompt = dedent(
            f"""
            Relacione os precedentes candidatos com a peticao e retorne uma sintese
            para cada precedente no formato estruturado esperado.

            Resumo da peticao:
            - case_summary: {petition_summary_dto.case_summary}
            - legal_issue: {petition_summary_dto.legal_issue}
            - central_question: {petition_summary_dto.central_question}
            - relevant_laws: {', '.join(petition_summary_dto.relevant_laws)}
            - key_facts: {', '.join(petition_summary_dto.key_facts)}
            - search_terms: {', '.join(petition_summary_dto.search_terms)}

            Precedentes candidatos:
            {precedents_input}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _persist_analysis_precedents_step(
        self,
        step_input: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessão', 'Session state is required')

        analysis_id = str(run_context.session_state.get('analysis_id', ''))
        filters_dto = run_context.session_state.get('filters_dto')
        raw_analysis_precedents = run_context.session_state.get('analysis_precedents')

        if not analysis_id:
            msg = 'Analysis id is required to persist analysis precedents'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(filters_dto, AnalysisPrecedentsSearchFiltersDto):
            msg = 'Analysis precedents filters are required to persist analysis precedents'
            raise AppError('Erro de execução do workflow', msg)

        if not isinstance(raw_analysis_precedents, list):
            msg = 'Analysis precedents are required to persist analysis precedents'
            raise AppError('Erro de execução do workflow', msg)

        analysis_precedents_candidates = cast('list[object]', raw_analysis_precedents)
        if not all(
            isinstance(analysis_precedent, AnalysisPrecedentDto)
            for analysis_precedent in analysis_precedents_candidates
        ):
            msg = 'Analysis precedents are required to persist analysis precedents'
            raise AppError('Erro de execução do workflow', msg)

        analysis_precedents = cast(
            'list[AnalysisPrecedentDto]',
            analysis_precedents_candidates,
        )

        self._create_analysis_precedents_use_case.execute(
            analysis_id=analysis_id,
            filters_dto=filters_dto,
            analysis_precedents=analysis_precedents,
            synthesis_output=step_input.get_last_step_content(),
        )

        return StepOutput(content='analysis-precedents-persisted')
