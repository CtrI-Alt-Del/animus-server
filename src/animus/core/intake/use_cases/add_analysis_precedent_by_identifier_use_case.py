from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PrecedentNotFoundError,
)
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_status_dto import (
    AnalysisStatusDto,
)
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.precedents_repository import PrecedentsRepository
from animus.core.shared.domain.structures import Id


class AddAnalysisPrecedentByIdentifierUseCase:
    def __init__(
        self,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        analyses_repository: AnalysesRepository,
        precedents_repository: PrecedentsRepository,
    ) -> None:
        self._analysis_precedents_repository = analysis_precedents_repository
        self._analyses_repository = analyses_repository
        self._precedents_repository = precedents_repository

    def execute(
        self,
        analysis_id: str,
        precedent_identifier_dto: PrecedentIdentifierDto,
    ) -> AnalysisStatusDto:
        analysis_id_vo = Id.create(analysis_id)

        analysis = self._analyses_repository.find_by_id(analysis_id_vo)

        if not analysis:
            raise AnalysisNotFoundError

        precedent = self._precedents_repository.find_by_identifier(
            PrecedentIdentifier.create(precedent_identifier_dto)
        )

        if not precedent:
            raise PrecedentNotFoundError

        existing_relation = (
            self._analysis_precedents_repository.find_by_analysis_id_and_precedent_id(
                analysis_id_vo,
                precedent.id,
            )
        )

        if existing_relation:
            self._analysis_precedents_repository.choose_by_analysis_id_and_precedent_id(
                analysis_id_vo,
                precedent.id,
            )
        else:
            dto = AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=precedent.dto,
                is_chosen=True,
                applicability_level=2,  # APPLICABLE
                is_manually_added=True,
            )
            analysis_precedent = AnalysisPrecedent.create(dto)
            self._analysis_precedents_repository.add_many_by_analysis_id(
                analysis_id_vo,
                [analysis_precedent],
            )

        # Re-fetch analysis to get updated status
        updated_analysis = self._analyses_repository.find_by_id(analysis_id_vo)

        if not updated_analysis:
            raise AnalysisNotFoundError

        return AnalysisStatusDto(value=updated_analysis.status.dto)
