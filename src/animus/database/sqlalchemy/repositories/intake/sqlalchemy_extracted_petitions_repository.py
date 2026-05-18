from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.extracted_petition import ExtractedPetition
from animus.core.intake.interfaces.extracted_petitions_repository import (
    ExtractedPetitionsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.extracted_petition_mapper import (
    ExtractedPetitionMapper,
)
from animus.database.sqlalchemy.models.intake.extracted_petition_model import (
    ExtractedPetitionModel,
)


class SqlalchemyExtractedPetitionsRepository(ExtractedPetitionsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(self, analysis_id: Id) -> ExtractedPetition | None:
        model = self._sqlalchemy.get(ExtractedPetitionModel, analysis_id.value)
        if model is None:
            return None

        return ExtractedPetitionMapper.to_entity(model)

    def add(self, extracted_petition: ExtractedPetition) -> None:
        self._sqlalchemy.add(ExtractedPetitionMapper.to_model(extracted_petition))

    def replace(self, extracted_petition: ExtractedPetition) -> None:
        model = self._sqlalchemy.get(
            ExtractedPetitionModel,
            extracted_petition.analysis_id.value,
        )
        if model is None:
            self.add(extracted_petition)
            return

        model.first_page = extracted_petition.first_page.value
        model.last_page = extracted_petition.last_page.value
