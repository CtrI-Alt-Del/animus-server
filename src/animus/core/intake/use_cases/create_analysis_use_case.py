from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.shared.domain.structures import Datetime, Id, Logical


class CreateAnalysisUseCase:
    def __init__(self, analyses_repository: AnalysesRepository) -> None:
        self._analyses_repository = analyses_repository

    def execute(
        self,
        account_id: str,
        type: str = 'FIRST_INSTANCE',
        folder_id: str | None = None,
    ) -> AnalysisDto:
        normalized_account_id = Id.create(account_id)
        normalized_type = AnalysisType.normalize(type)
        normalized_folder_id = Id.create(folder_id) if folder_id is not None else None
        next_number = self._analyses_repository.find_next_generated_name_number(
            normalized_account_id
        )

        initial_status = (
            SecondInstanceAnalysisStatus.create_as_waiting_document_upload()
            if normalized_type.is_second_instance.is_true
            else CaseAssessmentAnalysisStatus.create_as_waiting_document_upload()
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
                type=normalized_type.dto,
                status=initial_status.dto,
                is_archived=Logical.create_false().value,
                created_at=Datetime.create_at_now().value.isoformat(),
            )
        )

        self._analyses_repository.add(analysis)

        return analysis.dto
