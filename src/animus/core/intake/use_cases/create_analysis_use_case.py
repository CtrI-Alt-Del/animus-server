from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.shared.domain.structures import Datetime, Id, Logical


class CreateAnalysisUseCase:
    def __init__(self, analisyses_repository: AnalisysesRepository) -> None:
        self._analisyses_repository = analisyses_repository

    def execute(self, account_id: str, folder_id: str | None = None) -> AnalysisDto:
        normalized_account_id = Id.create(account_id)
        normalized_folder_id = Id.create(folder_id) if folder_id is not None else None
        next_number = self._analisyses_repository.find_next_generated_name_number(
            normalized_account_id
        )
        analysis = Analysis.create(
            AnalysisDto(
                name=f'Nova analise #{next_number.value}',
                folder_id=(
                    normalized_folder_id.value
                    if normalized_folder_id is not None
                    else None
                ),
                account_id=normalized_account_id.value,
                status=AnalysisStatusValue.WAITING_PETITION.value,
                is_archived=Logical.create_false().value,
                created_at=Datetime.create_at_now().value.isoformat(),
            )
        )

        self._analisyses_repository.add(analysis)

        return analysis.dto
