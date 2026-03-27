from animus.core.intake.domain.entities.analysis_status import AnalysisStatus
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.entities.dtos.analysis_status_dto import (
    AnalysisStatusDto,
)
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.structures import Datetime, Id, Logical, Name


@entity
class Analysis(Entity):
    name: Name
    folder_id: Id | None
    account_id: Id
    status: AnalysisStatus
    is_archived: Logical
    created_at: Datetime

    @classmethod
    def create(cls, dto: AnalysisDto) -> 'Analysis':
        folder_id = Id.create(dto.folder_id) if dto.folder_id is not None else None

        return cls(
            id=Id.create(dto.id),
            name=Name.create(dto.name),
            folder_id=folder_id,
            account_id=Id.create(dto.account_id),
            status=AnalysisStatus.create(AnalysisStatusDto(value=dto.status)),
            is_archived=Logical.create(dto.is_archived),
            created_at=Datetime.create(dto.created_at),
        )

    @property
    def dto(self) -> AnalysisDto:
        return AnalysisDto(
            id=self.id.value,
            name=self.name.value,
            folder_id=self.folder_id.value if self.folder_id is not None else None,
            account_id=self.account_id.value,
            status=self.status.value.value,
            is_archived=self.is_archived.value,
            created_at=self.created_at.value.isoformat(),
        )
