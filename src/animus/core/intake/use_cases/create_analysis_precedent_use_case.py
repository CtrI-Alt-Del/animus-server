from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.errors.precedent_not_found_error import (
    PrecedentNotFoundError,
)
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    PrecedentsRepository,
)
from animus.core.shared.domain.structures import Id


class CreateAnalysisPrecedentUseCase:
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
        is_manually_added: bool,
    ) -> AnalysisPrecedentDto:
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        precedent_identifier = PrecedentIdentifier.create(precedent_identifier_dto)
        precedent = self._precedents_repository.find_by_identifier(precedent_identifier)
        if precedent is None:
            raise PrecedentNotFoundError

        existing_analysis_precedent = (
            self._analysis_precedents_repository.find_by_analysis_id_and_precedent_id(
                analysis_id=analysis_id_entity,
                precedent_id=precedent.id,
            )
        )
        if existing_analysis_precedent is not None:
            return existing_analysis_precedent.dto

        analysis_precedent = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=precedent.dto,
                is_manually_added=is_manually_added,
                is_chosen=True,
            )
        )
        self._analysis_precedents_repository.add_many_by_analysis_id(
            analysis_id=analysis_id_entity,
            analysis_precedents=[analysis_precedent],
        )

        return analysis_precedent.dto
