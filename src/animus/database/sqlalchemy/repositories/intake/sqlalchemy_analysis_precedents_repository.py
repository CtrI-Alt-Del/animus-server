from sqlalchemy import delete, desc, select, update
from sqlalchemy.orm import Session, joinedload

from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.interfaces import AnalysisPrecedentsRepository
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse
from animus.database.sqlalchemy.mappers.intake import AnalysisPrecedentMapper
from animus.database.sqlalchemy.models.intake import AnalysisPrecedentModel


class SqlalchemyAnalysisPrecedentsRepository(AnalysisPrecedentsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_many_by_analysis_id(
        self, analysis_id: Id
    ) -> ListResponse[AnalysisPrecedent]:
        models = self._sqlalchemy.scalars(
            select(AnalysisPrecedentModel)
            .options(
                joinedload(AnalysisPrecedentModel.precedent),
                joinedload(AnalysisPrecedentModel.legal_features),
            )
            .where(AnalysisPrecedentModel.analysis_id == analysis_id.value)
            .order_by(
                AnalysisPrecedentModel.final_rank.asc(),
                desc(AnalysisPrecedentModel.similarity_score),
                AnalysisPrecedentModel.precedent_id.asc(),
            )
        ).all()

        return ListResponse(
            items=[AnalysisPrecedentMapper.to_entity(model) for model in models]
        )

    def find_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> AnalysisPrecedent | None:
        model = self._sqlalchemy.scalar(
            select(AnalysisPrecedentModel)
            .options(
                joinedload(AnalysisPrecedentModel.precedent),
                joinedload(AnalysisPrecedentModel.legal_features),
            )
            .where(
                AnalysisPrecedentModel.analysis_id == analysis_id.value,
                AnalysisPrecedentModel.precedent_id == precedent_id.value,
            )
        )
        if model is None:
            return None

        return AnalysisPrecedentMapper.to_entity(model)

    def remove_many_by_analysis_id(self, analysis_id: Id) -> None:
        self._sqlalchemy.execute(
            delete(AnalysisPrecedentModel).where(
                AnalysisPrecedentModel.analysis_id == analysis_id.value
            )
        )

    def add_many_by_analysis_id(
        self,
        analysis_id: Id,
        analysis_precedents: list[AnalysisPrecedent],
    ) -> None:
        models = [
            AnalysisPrecedentMapper.to_model(analysis_precedent)
            for analysis_precedent in analysis_precedents
        ]
        for model in models:
            model.analysis_id = analysis_id.value

        self._sqlalchemy.add_all(models)

    def choose_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> None:
        self._sqlalchemy.execute(
            update(AnalysisPrecedentModel)
            .where(AnalysisPrecedentModel.analysis_id == analysis_id.value)
            .values(is_chosen=False)
        )
        self._sqlalchemy.execute(
            update(AnalysisPrecedentModel)
            .where(
                AnalysisPrecedentModel.analysis_id == analysis_id.value,
                AnalysisPrecedentModel.precedent_id == precedent_id.value,
            )
            .values(is_chosen=True)
        )
