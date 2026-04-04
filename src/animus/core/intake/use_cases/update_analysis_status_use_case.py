from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatus
from animus.core.intake.domain.entities.dtos import AnalysisDto, AnalysisStatusDto
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.interfaces import AnalisysesRepository
from animus.core.shared.domain.structures import Id


class UpdateAnalysisStatusUseCase:
    def __init__(self, analisyses_repository: AnalisysesRepository) -> None:
        self._analisyses_repository = analisyses_repository

    def execute(self, analysis_id: str, status: str) -> None:
        print("update analysis status", status)
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)

        if analysis is None:
            raise AnalysisNotFoundError

        analysis_status = AnalysisStatus.create(AnalysisStatusDto(value=status))
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
