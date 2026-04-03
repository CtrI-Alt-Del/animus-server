from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatus
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos import AnalysisDto, AnalysisStatusDto
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.domain.structures.dtos import PrecedentIdentifierDto
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.domain.errors.precedent_not_found_error import (
    PrecedentNotFoundError,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
)
from animus.core.shared.domain.structures import Id


class ChooseAnalysisPrecedentUseCase:
    def __init__(
        self,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        analisyses_repository: AnalisysesRepository,
    ) -> None:
        self._analysis_precedents_repository = analysis_precedents_repository
        self._analisyses_repository = analisyses_repository

    def execute(
        self,
        analysis_id: str,
        precedent_identifier_dto: PrecedentIdentifierDto,
    ) -> AnalysisStatusDto:
        analysis_id_entity = Id.create(analysis_id)
        precedent_identifier = PrecedentIdentifier.create(precedent_identifier_dto)
        analysis_precedents = (
            self._analysis_precedents_repository.find_many_by_analysis_id(
                analysis_id=analysis_id_entity,
            )
        )

        analysis_precedent = next(
            (
                item
                for item in analysis_precedents.items
                if item.precedent.identifier == precedent_identifier
            ),
            None,
        )

        if analysis_precedent is None:
            raise PrecedentNotFoundError

        self._analysis_precedents_repository.choose_by_analysis_id_and_precedent_id(
            analysis_id=analysis_id_entity,
            precedent_id=analysis_precedent.precedent.id,
        )

        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        analysis_status = AnalysisStatus.create(
            AnalysisStatusDto(value=AnalysisStatusValue.PRECEDENT_CHOSED.value)
        )
        updated_analysis = Analysis.create(
            AnalysisDto(
                id=analysis.id.value,
                name=analysis.name.value,
                folder_id=(
                    analysis.folder_id.value if analysis.folder_id is not None else None
                ),
                account_id=analysis.account_id.value,
                status=analysis_status.value.value,
                is_archived=analysis.is_archived.value,
                created_at=analysis.created_at.value.isoformat(),
            )
        )
        self._analisyses_repository.replace(updated_analysis)

        return updated_analysis.status.dto
