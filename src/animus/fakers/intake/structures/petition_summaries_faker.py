from faker import Faker

from animus.core.intake.domain.structures import PetitionSummary
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)


class PetitionSummariesFaker:
    _faker = Faker()

    @staticmethod
    def fake(
        content: str | None = None,
        main_points: list[str] | None = None,
    ) -> PetitionSummary:
        return PetitionSummary.create(
            PetitionSummariesFaker.fake_dto(
                content=content,
                main_points=main_points,
            )
        )

    @staticmethod
    def fake_dto(
        content: str | None = None,
        main_points: list[str] | None = None,
    ) -> PetitionSummaryDto:
        generated_main_points = main_points or [
            PetitionSummariesFaker._faker.sentence(nb_words=8) for _ in range(3)
        ]

        return PetitionSummaryDto(
            content=content or PetitionSummariesFaker._faker.paragraph(nb_sentences=4),
            main_points=generated_main_points,
        )

    @staticmethod
    def fake_many(count: int) -> list[PetitionSummary]:
        return [PetitionSummariesFaker.fake() for _ in range(count)]

    @staticmethod
    def fake_many_dto(count: int) -> list[PetitionSummaryDto]:
        return [PetitionSummariesFaker.fake_dto() for _ in range(count)]
