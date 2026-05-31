from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    DraftRegenerationCaseSummaryUnavailableError,
    DraftRegenerationChosenPrecedentsRequiredError,
    DraftRegenerationCommentsRequiredError,
    InconsistentAnalysisTypeError,
    PetitionDraftRegenerationUnavailableError,
)
from animus.core.intake.domain.events import (
    PetitionDraftRegenerationTriggeredEvent,
)
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    PetitionDraftsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TriggerPetitionDraftRegenerationUseCase:
    def __init__(
        self,
        analyses_repository: AnalysesRepository,
        petition_drafts_repository: PetitionDraftsRepository,
        case_summaries_repository: CaseSummariesRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        broker: Broker,
    ) -> None:
        self._analyses_repository = analyses_repository
        self._petition_drafts_repository = petition_drafts_repository
        self._case_summaries_repository = case_summaries_repository
        self._analysis_precedents_repository = analysis_precedents_repository
        self._broker = broker

    def execute(self, analysis_id: str, comments: str) -> None:
        analysis_id_entity = Id.create(analysis_id)
        normalized_comments = comments.strip()
        if normalized_comments == '':
            raise DraftRegenerationCommentsRequiredError

        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_case_analysis.is_false:
            raise InconsistentAnalysisTypeError

        petition_draft = self._petition_drafts_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if petition_draft is None:
            raise PetitionDraftRegenerationUnavailableError

        case_summary = self._case_summaries_repository.find_by_analysis_id(
            analysis_id_entity,
        )
        if case_summary is None:
            raise DraftRegenerationCaseSummaryUnavailableError

        analysis_precedents_response = (
            self._analysis_precedents_repository.find_many_by_analysis_id(
                analysis_id_entity,
            )
        )
        if not any(
            analysis_precedent.is_chosen.is_true
            for analysis_precedent in analysis_precedents_response.items
        ):
            raise DraftRegenerationChosenPrecedentsRequiredError

        analysis.set_status(
            CaseAssessmentAnalysisStatus.create_as_generating_petition_draft()
        )
        self._analyses_repository.replace(analysis)

        self._broker.publish(
            PetitionDraftRegenerationTriggeredEvent(
                analysis_id=analysis_id_entity.value,
                comments=normalized_comments,
            )
        )
