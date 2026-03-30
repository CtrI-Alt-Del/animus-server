from datetime import UTC, datetime

from faker import Faker

from animus.core.intake.domain.entities import Petition
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.shared.domain.structures import Id


class PetitionsFaker:
    _faker = Faker()

    @staticmethod
    def fake(
        petition_id: str | None = None,
        analysis_id: str | None = None,
        uploaded_at: str | None = None,
        document: PetitionDocumentDto | None = None,
    ) -> Petition:
        return Petition.create(
            PetitionsFaker.fake_dto(
                petition_id=petition_id,
                analysis_id=analysis_id,
                uploaded_at=uploaded_at,
                document=document,
            )
        )

    @staticmethod
    def fake_dto(
        petition_id: str | None = None,
        analysis_id: str | None = None,
        uploaded_at: str | None = None,
        document: PetitionDocumentDto | None = None,
    ) -> PetitionDto:
        return PetitionDto(
            id=petition_id or Id.create().value,
            analysis_id=analysis_id or Id.create().value,
            uploaded_at=uploaded_at or datetime.now(UTC).isoformat(),
            document=document
            or PetitionDocumentDto(
                file_path=PetitionsFaker._faker.file_path(
                    depth=3,
                    category='text',
                    extension='pdf',
                ),
                name=PetitionsFaker._faker.file_name(
                    category='text',
                    extension='pdf',
                ),
            ),
        )

    @staticmethod
    def fake_many(count: int) -> list[Petition]:
        return [PetitionsFaker.fake() for _ in range(count)]

    @staticmethod
    def fake_many_dto(count: int) -> list[PetitionDto]:
        return [PetitionsFaker.fake_dto() for _ in range(count)]
