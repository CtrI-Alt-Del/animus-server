from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel


class AnalysisMapper:
    @staticmethod
    def to_entity(model: AnalysisModel) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=model.id,
                name=model.name,
                folder_id=model.folder_id,
                account_id=model.account_id,
                status=model.status,
                is_archived=model.is_archived,
                created_at=model.created_at.isoformat(),
            )
        )

    @staticmethod
    def to_model(entity: Analysis) -> AnalysisModel:
        return AnalysisModel(
            id=entity.id.value,
            name=entity.name.value,
            folder_id=entity.folder_id.value if entity.folder_id is not None else None,
            account_id=entity.account_id.value,
            status=entity.status.value.value,
            is_archived=entity.is_archived.value,
            created_at=entity.created_at.value,
        )
