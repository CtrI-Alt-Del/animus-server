from typing import TYPE_CHECKING

from dataclasses import replace

from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.domain.errors.petition_not_found_error import (
    PetitionNotFoundError,
)
from animus.core.intake.domain.errors.petition_summary_unavailable_error import (
    PetitionSummaryUnavailableError,
)
from animus.core.intake.domain.structures.analysis_report import AnalysisReport
from animus.core.intake.domain.structures.dtos.analysis_report_dto import (
    AnalysisReportDto,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.shared.domain.errors.forbidden_error import ForbiddenError
from animus.core.shared.domain.structures import Id, Text

if TYPE_CHECKING:
    from animus.core.intake.domain.structures.analysis_precedent import (
        AnalysisPrecedent,
    )


class GetAnalysisReportUseCase:
    def __init__(
        self,
        analisyses_repository: AnalisysesRepository,
        petitions_repository: PetitionsRepository,
        petition_summaries_repository: PetitionSummariesRepository,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
    ) -> None:
        self._analisyses_repository = analisyses_repository
        self._petitions_repository = petitions_repository
        self._petition_summaries_repository = petition_summaries_repository
        self._analysis_precedents_repository = analysis_precedents_repository

    def execute(self, analysis_id: str, account_id: str) -> AnalysisReportDto:
        id_analysis = Id.create(analysis_id)
        id_account = Id.create(account_id)

        analysis = self._analisyses_repository.find_by_id(id_analysis)

        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.account_id != id_account:
            raise ForbiddenError('Esta analise nao pertence a sua conta.')

        petition = self._petitions_repository.find_by_analysis_id(id_analysis)
        if petition is None:
            raise PetitionNotFoundError

        summary = self._petition_summaries_repository.find_by_analysis_id(id_analysis)
        if summary is None:
            raise PetitionSummaryUnavailableError

        analysis_precedents_response = (
            self._analysis_precedents_repository.find_many_by_analysis_id(id_analysis)
        )

        classified_precedents: list[AnalysisPrecedent] = []
        for precedent in analysis_precedents_response.items:
            applicability = (
                precedent.applicability_percentage.value
                if precedent.applicability_percentage
                else None
            )
            classification = self._classify_precedent(applicability)
            classified_precedents.append(
                replace(precedent, classification_level=Text.create(classification))
            )

        report = AnalysisReport(
            analysis=analysis,
            petition=petition,
            summary=summary,
            precedents=classified_precedents,
        )

        return report.dto

    def _classify_precedent(self, applicability_percentage: float | None) -> str:
        if applicability_percentage is None:
            return 'NOT_APPLICABLE'

        if applicability_percentage >= 85.0:
            return 'APPLICABLE'

        if applicability_percentage >= 70.0:
            return 'POSSIBLY_APPLICABLE'

        return 'NOT_APPLICABLE'
