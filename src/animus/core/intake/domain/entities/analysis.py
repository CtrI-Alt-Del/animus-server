from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFilters,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
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
        analysis_type = AnalysisType.create(dto.type)

        return cls(
            id=Id.create(dto.id),
            name=Name.create(dto.name),
            folder_id=folder_id,
            account_id=Id.create(dto.account_id),
            type=analysis_type,
            status=cls._normalize_status(analysis_type, dto.status),
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
            type=self.type.dto,
            status=self.status.dto,
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

    def unarchive(self) -> None:
        self.is_archived = Logical.create_false()

    def set_status(self, status: AnalysisStatus | str) -> None:
        if isinstance(status, str):
            self.status = self._normalize_status(self.type, status)
            return

        self.status = status

    def set_precedents_search_filters(
        self,
        dto: AnalysisPrecedentsSearchFiltersDto,
    ) -> None:
        self.precedents_search_filters = AnalysisPrecedentsSearchFilters.create(dto)

    def move_to_folder(self, folder_id: Id | None) -> None:
        self.folder_id = folder_id

    @classmethod
    def _normalize_status(cls, type: AnalysisType, status: str) -> AnalysisStatus:
        if type.is_case_analysis.is_true:
            return CaseAssessmentAnalysisStatus.create(status)
        if type.is_first_instance.is_true:
            return FirstInstanceAnalysisStatus.create(status)
        if type.is_second_instance.is_true:
            return SecondInstanceAnalysisStatus.create(status)

        raise ValueError(f'Tipo de analise invalido: {type.dto}')
