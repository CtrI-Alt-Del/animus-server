from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.entities.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.entities.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.domain.entities.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFilters,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Datetime, Id, Logical, Name

AnalysisStatus = (
    CaseAssessmentAnalysisStatus
    | FirstInstanceAnalysisStatus
    | SecondInstanceAnalysisStatus
)


@entity
class Analysis(Entity):
    name: Name
    folder_id: Id | None
    account_id: Id
    type: AnalysisType
    status: AnalysisStatus
    is_archived: Logical
    precedents_search_filters: AnalysisPrecedentsSearchFilters | None
    created_at: Datetime

    @classmethod
    def create(cls, dto: AnalysisDto) -> 'Analysis':
        folder_id = Id.create(dto.folder_id) if dto.folder_id is not None else None
        precedents_search_filters = (
            AnalysisPrecedentsSearchFilters.create(dto.precedents_search_filters)
            if dto.precedents_search_filters is not None
            else None
        )

        return cls(
            id=Id.create(dto.id),
            name=Name.create(dto.name),
            folder_id=folder_id,
            account_id=Id.create(dto.account_id),
            type=AnalysisType.normalize(dto.type),
            status=cls._normalize_status(dto.type, dto.status),
            is_archived=Logical.create(dto.is_archived),
            precedents_search_filters=precedents_search_filters,
            created_at=Datetime.create(dto.created_at),
        )

    @property
    def dto(self) -> AnalysisDto:
        return AnalysisDto(
            id=self.id.value,
            name=self.name.value,
            folder_id=self.folder_id.value if self.folder_id is not None else None,
            account_id=self.account_id.value,
            type=self.type,
            status=self.status,
            is_archived=self.is_archived.value,
            precedents_search_filters=(
                self.precedents_search_filters.dto
                if self.precedents_search_filters is not None
                else None
            ),
            created_at=self.created_at.value.isoformat(),
        )

    def rename(self, name: str) -> None:
        self.name = Name.create(name)

    def archive(self) -> None:
        self.is_archived = Logical.create_true()

    def set_status(self, status: str | AnalysisStatus) -> None:
        self.status = self._normalize_status(self.type, status)

    def set_precedents_search_filters(
        self,
        dto: AnalysisPrecedentsSearchFiltersDto,
    ) -> None:
        self.precedents_search_filters = AnalysisPrecedentsSearchFilters.create(dto)

    def move_to_folder(self, folder_id: Id | None) -> None:
        self.folder_id = folder_id

    @staticmethod
    def _normalize_status(
        analysis_type: AnalysisType,
        status: str | CaseAssessmentAnalysisStatus | SecondInstanceAnalysisStatus,
    ) -> AnalysisStatus:
        normalized_status = Analysis._normalize_legacy_status(status)

        normalized_analysis_type = AnalysisType.normalize(analysis_type)

        if normalized_analysis_type.uses_case_assessment_or_first_instance_flow():
            try:
                return CaseAssessmentAnalysisStatus(normalized_status)
            except ValueError as error:
                raise ValidationError(
                    'Status de analise invalido para analise de case '
                    'assessment ou primeira '
                    f'instancia: {normalized_status}'
                ) from error

        try:
            return SecondInstanceAnalysisStatus(normalized_status)
        except ValueError as error:
            raise ValidationError(
                'Status de analise invalido para analise de segunda '
                f'instancia: {normalized_status}'
            ) from error

    @staticmethod
    def _normalize_legacy_status(
        status: str | CaseAssessmentAnalysisStatus | SecondInstanceAnalysisStatus,
    ) -> str:
        legacy_mapping = {
            'WAITING_PETITION': CaseAssessmentAnalysisStatus.WAITING_DOCUMENT_UPLOAD.value,
            'PETITION_UPLOADED': CaseAssessmentAnalysisStatus.DOCUMENT_UPLOADED.value,
            'ANALYZING_PETITION': CaseAssessmentAnalysisStatus.ANALYZING_CASE.value,
            'PETITION_ANALYZED': CaseAssessmentAnalysisStatus.CASE_ANALYZED.value,
            'WAITING_PRECEDENT_CHOISE': CaseAssessmentAnalysisStatus.DONE.value,
            'PRECEDENT_CHOSED': CaseAssessmentAnalysisStatus.DONE.value,
            'ANALYZING_PRECEDENTS_SIMILARITY': (
                CaseAssessmentAnalysisStatus.SEARCHING_PRECEDENTS.value
            ),
            'ANALYZING_PRECEDENTS_APPLICABILITY': (
                CaseAssessmentAnalysisStatus.SEARCHING_PRECEDENTS.value
            ),
            'GENERATING_SYNTHESIS': (
                CaseAssessmentAnalysisStatus.GENERATING_PETITION_DRAFT.value
            ),
        }

        normalized_status = str(status)
        return legacy_mapping.get(normalized_status, normalized_status)
