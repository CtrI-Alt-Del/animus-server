from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    InconsistentAnalysisTypeError,
    PetitionDraftExportIncompleteError,
    PetitionDraftUnavailableError,
)
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.intake.interfaces import (
    AnalysesRepository,
    PetitionDraftDocxProvider,
    PetitionDraftsRepository,
)
from animus.core.shared.domain.structures import Id


class ExportPetitionDraftDocxUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        petition_drafts_repository: PetitionDraftsRepository,
        petition_draft_docx_provider: PetitionDraftDocxProvider,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._petition_drafts_repository = petition_drafts_repository
        self._petition_draft_docx_provider = petition_draft_docx_provider

    def execute(self, analysis_id: str) -> AnalysisDocumentDto:
        analysis_id_entity = Id.create(analysis_id)

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_case_analysis.is_false:
            raise InconsistentAnalysisTypeError

        petition_draft = self._petition_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if petition_draft is None:
            raise PetitionDraftUnavailableError

        missing_fields = self._collect_missing_fields(petition_draft)
        if missing_fields:
            raise PetitionDraftExportIncompleteError(missing_fields)

        return self._petition_draft_docx_provider.export(
            analysis.id.value,
            analysis.name.value,
            petition_draft,
        )

    def _collect_missing_fields(self, petition_draft: PetitionDraft) -> list[str]:
        missing_fields: list[str] = []

        if petition_draft.structured_facts.value.strip() == '':
            missing_fields.append('structured_facts')

        if petition_draft.legal_grounds.value.strip() == '':
            missing_fields.append('legal_grounds')

        if petition_draft.central_thesis.value.strip() == '':
            missing_fields.append('central_thesis')

        if len(petition_draft.requests) == 0 or any(
            request.value.strip() == '' for request in petition_draft.requests
        ):
            missing_fields.append('requests')

        if len(petition_draft.precedent_citations) == 0 or any(
            precedent_citation.value.strip() == ''
            for precedent_citation in petition_draft.precedent_citations
        ):
            missing_fields.append('precedent_citations')

        return missing_fields
