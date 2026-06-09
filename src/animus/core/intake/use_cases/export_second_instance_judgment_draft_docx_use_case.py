from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    ChosenAnalysisPrecedentsRequiredError,
    SecondInstanceAnalysisRequiredError,
    SecondInstanceDecisionNotFoundError,
    SecondInstanceJudgmentDraftExportIncompleteError,
    SecondInstanceJudgmentDraftUnavailableError,
)
from animus.core.intake.domain.structures import SecondInstanceJudgmentDraft
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    SecondInstanceDecisionsRepository,
    SecondInstanceJudgmentDraftDocxProvider,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.shared.domain.structures import Id


class ExportSecondInstanceJudgmentDraftDocxUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        judgment_drafts_repository: SecondInstanceJudgmentDraftsRepository,
        second_instance_decisions_repository: SecondInstanceDecisionsRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        second_instance_judgment_draft_docx_provider: SecondInstanceJudgmentDraftDocxProvider,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._judgment_drafts_repository = judgment_drafts_repository
        self._second_instance_decisions_repository = (
            second_instance_decisions_repository
        )
        self._analysis_precedents_repository = analysis_precedents_repository
        self._second_instance_judgment_draft_docx_provider = (
            second_instance_judgment_draft_docx_provider
        )

    def execute(self, analysis_id: str) -> AnalysisDocumentDto:
        analysis_id_entity = Id.create(analysis_id)

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_second_instance.is_false:
            raise SecondInstanceAnalysisRequiredError

        judgment_draft = self._judgment_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if judgment_draft is None:
            raise SecondInstanceJudgmentDraftUnavailableError

        missing_fields = self._collect_missing_fields(judgment_draft)
        if missing_fields:
            raise SecondInstanceJudgmentDraftExportIncompleteError(missing_fields)

        second_instance_decision = (
            self._second_instance_decisions_repository.find_by_analysis_id(
                analysis_id_entity,
            )
        )
        if second_instance_decision is None:
            raise SecondInstanceDecisionNotFoundError

        analysis_precedents = (
            self._analysis_precedents_repository.find_many_by_analysis_id(
                analysis_id_entity,
            )
        )
        chosen_precedents = [
            precedent
            for precedent in analysis_precedents.items
            if precedent.is_chosen.is_true
        ]
        if len(chosen_precedents) == 0:
            raise ChosenAnalysisPrecedentsRequiredError

        return self._second_instance_judgment_draft_docx_provider.export(
            analysis.id.value,
            analysis.name.value,
            judgment_draft,
            second_instance_decision,
            chosen_precedents,
        )

    def _collect_missing_fields(
        self,
        judgment_draft: SecondInstanceJudgmentDraft,
    ) -> list[str]:
        missing_fields: list[str] = []

        if judgment_draft.report.value.strip() == '':
            missing_fields.append('report')

        if judgment_draft.merit_analysis.value.strip() == '':
            missing_fields.append('merit_analysis')

        if judgment_draft.precedent_adherence_analysis.value.strip() == '':
            missing_fields.append('precedent_adherence_analysis')

        if len(judgment_draft.ruling) == 0 or any(
            ruling_item.value.strip() == '' for ruling_item in judgment_draft.ruling
        ):
            missing_fields.append('ruling')

        return missing_fields
