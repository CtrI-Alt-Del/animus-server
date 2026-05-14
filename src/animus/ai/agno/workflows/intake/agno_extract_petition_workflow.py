from collections.abc import Mapping
from textwrap import dedent
from typing import TYPE_CHECKING, Any, NamedTuple, cast
import logging

from agno.run.base import RunContext
from agno.workflow import Step, StepInput, StepOutput, Workflow

from animus.ai.agno.outputs.intake import PetitionExtractionOutput
from animus.ai.agno.squads import IntakeSquad
from animus.core.intake.domain.errors import PetitionExtractionNotFoundError
from animus.core.intake.domain.structures.dtos.petition_extraction_dto import (
    PetitionExtractionDto,
)
from animus.core.intake.interfaces import ExtractPetitionWorkflow
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Integer
from animus.core.storage.domain.structures import File
from animus.core.storage.interfaces import PdfProvider

if TYPE_CHECKING:
    from agno.workflow.step import StepExecutor


class _StepNames(NamedTuple):
    BUILD_EXTRACTION_INPUT: str = 'build-extraction-input'
    EXTRACT_PETITION: str = 'extract-petition'


class AgnoExtractPetitionWorkflow(ExtractPetitionWorkflow):
    def __init__(self, pdf_provider: PdfProvider) -> None:
        self._pdf_provider = pdf_provider
        self._team = IntakeSquad()
        self._step_names = _StepNames()
        self._window_size = 5

    def run(self, pdf_file: File) -> PetitionExtractionDto:
        total_pages = self._pdf_provider.count_pages(pdf_file).value
        if total_pages < 1:
            raise PetitionExtractionNotFoundError

        first_page: int | None = None
        last_page: int | None = None
        history: list[str] = []

        for start in range(1, total_pages + 1, self._window_size):
            end = min(start + self._window_size - 1, total_pages)
            pages_text = self._pdf_provider.extract_pages(
                pdf_file,
                Integer.create(start),
                Integer.create(end),
            )

            workflow = Workflow(
                name='extract-petition-window',
                steps=[
                    Step(
                        name=self._step_names.BUILD_EXTRACTION_INPUT,
                        executor=cast(
                            'StepExecutor', self._build_extraction_input_step
                        ),
                    ),
                    Step(
                        name=self._step_names.EXTRACT_PETITION,
                        agent=self._team.petition_extractor_agent,
                    ),
                ],
                session_state={
                    'total_pages': total_pages,
                    'start': start,
                    'end': end,
                    'pages_text': pages_text.value,
                    'history': history,
                    'first_page': first_page,
                    'last_page': last_page,
                },
            )

            output = workflow.run(input='start')
            extraction_output = self._normalize_extraction_output(output.content)

            if extraction_output.first_page is not None and first_page is None:
                first_page = extraction_output.first_page

            if extraction_output.last_page is not None:
                last_page = extraction_output.last_page

            logging.info(
                f'janela {start}-{end}: first_page={extraction_output.first_page}, '
                f'last_page={extraction_output.last_page}',
            )

            history.append(
                f'janela {start}-{end}: first_page={extraction_output.first_page}, '
                f'last_page={extraction_output.last_page}'
            )

            if first_page is not None and last_page is not None:
                break

        if first_page is None or last_page is None:
            raise PetitionExtractionNotFoundError

        if first_page < 1 or last_page < first_page or last_page > total_pages:
            msg = 'Limites de petição invalidados durante a extracao'
            raise AppError('Erro de execução do workflow', msg)

        return PetitionExtractionDto(
            first_page=first_page,
            last_page=last_page,
        )

    def _build_extraction_input_step(
        self,
        _: StepInput,
        run_context: RunContext,
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Erro de sessao', 'Session state is required')

        total_pages = int(run_context.session_state.get('total_pages', 0))
        start = int(run_context.session_state.get('start', 0))
        end = int(run_context.session_state.get('end', 0))
        pages_text = str(run_context.session_state.get('pages_text', ''))
        history = cast('list[str]', run_context.session_state.get('history', []))
        first_page = run_context.session_state.get('first_page')
        last_page = run_context.session_state.get('last_page')

        history_text = '\n'.join(history) if history else 'sem historico'
        first_page_text = str(first_page) if first_page is not None else 'null'
        last_page_text = str(last_page) if last_page is not None else 'null'

        prompt = dedent(
            f"""
            Analise a janela de paginas abaixo e atualize os limites da petição inicial.

            Total de paginas do PDF: {total_pages}
            Janela atual: {start}-{end}
            first_page atual: {first_page_text}
            last_page atual: {last_page_text}

            Historico de janelas anteriores:
            {history_text}

            Regras:
            - use numeros absolutos de pagina no PDF;
            - retorne null para campos sem evidencia;
            - first_page deve ser >= 1;
            - last_page deve ser >= first_page quando ambos existirem;
            - retorne somente o objeto estruturado.

            Conteudo textual da janela {start}-{end}:
            {pages_text}
            """
        ).strip()

        return StepOutput(content=prompt)

    def _normalize_extraction_output(self, output: object) -> PetitionExtractionOutput:
        unwrapped_output = self._unwrap_output_content(output)

        if isinstance(unwrapped_output, PetitionExtractionOutput):
            return unwrapped_output

        if isinstance(unwrapped_output, Mapping):
            data = cast(
                'dict[str, Any]', dict(cast('Mapping[str, object]', unwrapped_output))
            )
            return PetitionExtractionOutput(**data)

        msg = 'Invalid extraction output type from petition extractor workflow'
        raise AppError('Erro de execução do workflow', msg)

    def _unwrap_output_content(self, output_content: object) -> object:
        unwrapped_content: object = output_content
        for _ in range(6):
            if isinstance(unwrapped_content, (PetitionExtractionOutput, Mapping)):
                return cast('object', unwrapped_content)

            nested_content = getattr(unwrapped_content, 'content', None)
            if nested_content is None or nested_content is unwrapped_content:
                return unwrapped_content

            unwrapped_content = nested_content

        return unwrapped_content
