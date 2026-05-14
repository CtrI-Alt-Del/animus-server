from animus.core.intake.domain.structures.dtos.extracted_petition_dto import (
    ExtractedPetitionDto,
)
from animus.core.intake.domain.structures.extracted_petition import ExtractedPetition
from animus.database.sqlalchemy.models.intake.extracted_petition_model import (
    ExtractedPetitionModel,
)


class ExtractedPetitionMapper:
    @staticmethod
    def to_entity(model: ExtractedPetitionModel) -> ExtractedPetition:
        return ExtractedPetition.create(
            ExtractedPetitionDto(
                analysis_id=model.analysis_id,
                first_page=model.first_page,
                last_page=model.last_page,
            )
        )

    @staticmethod
    def to_model(extracted_petition: ExtractedPetition) -> ExtractedPetitionModel:
        return ExtractedPetitionModel(
            analysis_id=extracted_petition.analysis_id.value,
            first_page=extracted_petition.first_page.value,
            last_page=extracted_petition.last_page.value,
        )
