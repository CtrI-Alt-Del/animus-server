from typing import TYPE_CHECKING, NamedTuple, cast

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs import AnalysisPrecedentsSynthesisOutput
from animus.ai.agno.teams import IntakeTeam
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.interfaces.synthesize_analysis_precedents_workflow import (
    SynthesizeAnalysisPrecedentsWorkflow,
)
from animus.core.shared.domain.errors import AppError
from animus.core.shared.responses import ListResponse

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_SYNTHESIS_INPUT: str = "build-synthesis-input"
    SYNTHESIZE_ANALYSIS_PRECEDENTS: str = "synthesize-analysis-precedents"


class AgnoSynthesizeAnalysisPrecedentsWorkflow(SynthesizeAnalysisPrecedentsWorkflow):
    def __init__(self) -> None:
        self._team = IntakeTeam()
        self._step_names = _StepNames()

    def run(
        self,
        petition_summary: PetitionSummary,
        analysis_precedents: list[AnalysisPrecedentDto],
    ) -> ListResponse[AnalysisPrecedent]:
        if not analysis_precedents:
            return ListResponse(items=[])

        workflow = Workflow(
            name="synthesize-analysis-precedents",
            steps=[
                Step(
                    name=self._step_names.BUILD_SYNTHESIS_INPUT,
                    executor=cast("StepExecutor", self._build_synthesis_input_step),
                ),
                # Step(
                #     name=self._step_names.SYNTHESIZE_ANALYSIS_PRECEDENTS,
                #     agent=self._team.analysis_precedents_synthesizer_agent,
                # ),
            ],
            session_state={
                "petition_summary": petition_summary,
                "analysis_precedents": analysis_precedents,
            },
        )

        output = workflow.run(input="start")

        return ListResponse(items=cast("list[AnalysisPrecedent]", output.content))

    def _build_synthesis_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError("Erro de sessão", "Session state is required")

        petition_summary = run_context.session_state.get("petition_summary")
        analysis_precedents = run_context.session_state.get("analysis_precedents")

        if not isinstance(petition_summary, PetitionSummary):
            msg = "Petition summary is required to build precedents synthesis input"
            raise AppError("Erro de execução do workflow", msg)

        if not isinstance(analysis_precedents, list):
            msg = "Analysis precedents are required to build precedents synthesis input"
            raise AppError("Erro de execução do workflow", msg)

        analysis_precedents_dto = cast(
            "list[AnalysisPrecedentDto]", analysis_precedents
        )

        result: list[AnalysisPrecedent] = [
            AnalysisPrecedent.create(
                AnalysisPrecedentDto(
                    analysis_id=dto.analysis_id,
                    precedent=dto.precedent,
                    is_chosen=dto.is_chosen,
                    applicability_percentage=dto.applicability_percentage,
                    synthesis="",
                )
            )
            for dto in analysis_precedents_dto
        ]

        return StepOutput(content=result)

    def _normalize_synthesis_output(
        self,
        output: object,
    ) -> AnalysisPrecedentsSynthesisOutput:
        if isinstance(output, AnalysisPrecedentsSynthesisOutput):
            return output

        msg = "Invalid synthesis output type from analysis precedents workflow"
        raise AppError("Erro de execução do workflow", msg)

    def _merge_syntheses(
        self,
        analysis_precedents: list[AnalysisPrecedentDto],
        synthesis_output: AnalysisPrecedentsSynthesisOutput,
    ) -> ListResponse[AnalysisPrecedent]:
        syntheses_by_identifier: dict[tuple[str, str, int], str] = {}
        for item in synthesis_output.items:
            identifier_key = (item.court, item.kind, item.number)
            if identifier_key in syntheses_by_identifier:
                msg = "Duplicate precedent identifier returned by synthesis workflow"
                raise AppError("Erro de execução do workflow", msg)

            syntheses_by_identifier[identifier_key] = item.synthesis.strip()

        analysis_precedent_entities: list[AnalysisPrecedent] = []
        for analysis_precedent in analysis_precedents:
            identifier = analysis_precedent.precedent.identifier
            identifier_key = (
                identifier.court,
                identifier.kind,
                identifier.number,
            )
            synthesis = syntheses_by_identifier.get(identifier_key)
            if not synthesis:
                msg = "Missing synthesis for at least one precedent identifier"
                raise AppError("Erro de execução do workflow", msg)

            analysis_precedent_entities.append(
                AnalysisPrecedent.create(
                    AnalysisPrecedentDto(
                        analysis_id=analysis_precedent.analysis_id,
                        precedent=analysis_precedent.precedent,
                        is_chosen=analysis_precedent.is_chosen,
                        applicability_percentage=(
                            analysis_precedent.applicability_percentage
                        ),
                        synthesis=synthesis,
                    )
                )
            )

        return ListResponse(items=analysis_precedent_entities)
