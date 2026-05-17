from datetime import UTC, datetime

from faker import Faker

from animus.core.intake.domain.entities import Petition
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.shared.domain.structures import Id


class PetitionsFaker:
    _faker = Faker()

    @staticmethod
    def fake(
        petition_id: str | None = None,
        analysis_id: str | None = None,
        uploaded_at: str | None = None,
        document: AnalysisDocumentDto | None = None,
    ) -> Petition:
        normalized_analysis_id = analysis_id or Id.create().value
        normalized_uploaded_at = uploaded_at or datetime.now(UTC).isoformat()
        normalized_document = document or AnalysisDocumentDto(
            analysis_id=normalized_analysis_id,
            uploaded_at=normalized_uploaded_at,
            file_path=PetitionsFaker._faker.file_path(
                depth=3,
                category='text',
                extension='pdf',
            ),
            name=PetitionsFaker._faker.file_name(
                category='text',
                extension='pdf',
            ),
        )

        return Petition.create(
            petition_id=petition_id or Id.create().value,
            analysis_id=normalized_analysis_id,
            uploaded_at=normalized_uploaded_at,
            file_path=normalized_document.file_path,
            name=normalized_document.name,
        )

    @staticmethod
    def fake_many(count: int) -> list[Petition]:
        return [PetitionsFaker.fake() for _ in range(count)]
