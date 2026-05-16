from types import SimpleNamespace
from unittest.mock import create_autospec
from typing import Any

import pytest

from animus.ai.agno.outputs import PetitionSummaryOutput
from animus.ai.agno.workflows.intake import AgnoSummarizeFirstInstanceCaseWorkflow
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalisysesRepository,
    CaseSummariesRepository,
)
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Text


class TestAgnoSummarizeFirstInstanceCaseWorkflow:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.workflow = AgnoSummarizeFirstInstanceCaseWorkflow(
            case_summaries_repository=create_autospec(
                CaseSummariesRepository,
                instance=True,
            ),
            analysis_documents_repository=create_autospec(
                AnalysisDocumentsRepository,
                instance=True,
            ),
            analisyses_repository=create_autospec(
                AnalisysesRepository,
                instance=True,
            ),
        )

    def test_should_accept_petition_summary_output_from_agent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _run_workflow(*_args: object, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                content=PetitionSummaryOutput(
                    case_summary='Resumo',
                    legal_issue='Questao',
                    central_question='Pergunta',
                    relevant_laws=['Lei 1'],
                    key_facts=['Fato 1'],
                    search_terms=['Termo 1'],
                    requested_relief=['Pedido 1'],
                    excluded_or_accessory_topics=['Topico acessorio'],
                )
            )

        def _execute_create_case_summary(
            _self: object,
            analysis_id: str,
            dto: Any,
        ) -> Any:
            return dto

        monkeypatch.setattr(
            'animus.ai.agno.workflows.intake.agno_summarize_first_instance_case_workflow.Workflow.run',
            _run_workflow,
        )
        monkeypatch.setattr(
            'animus.ai.agno.workflows.intake.agno_summarize_first_instance_case_workflow.CreateCaseSummaryUseCase.execute',
            _execute_create_case_summary,
        )

        result = self.workflow.run(
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            document_content=Text.create('Documento de teste'),
        )

        assert result.case_summary == 'Resumo'
        assert result.requested_relief == ['Pedido 1']
        assert result.excluded_or_accessory_topics == ['Topico acessorio']

    def test_should_raise_when_output_type_is_invalid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _run_workflow_with_invalid_output(
            *_args: object,
            **_kwargs: object,
        ) -> SimpleNamespace:
            return SimpleNamespace(content='invalid-output')

        monkeypatch.setattr(
            'animus.ai.agno.workflows.intake.agno_summarize_first_instance_case_workflow.Workflow.run',
            _run_workflow_with_invalid_output,
        )

        with pytest.raises(AppError, match='Invalid summary output type'):
            self.workflow.run(
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                document_content=Text.create('Documento de teste'),
            )
