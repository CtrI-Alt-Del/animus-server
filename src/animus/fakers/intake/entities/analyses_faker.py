from faker import Faker
from datetime import UTC, datetime

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.shared.domain.structures import Id


class AnalysesFaker:
    _faker = Faker()
    _default_status = AnalysisStatusValue.WAITING_PETITION.value

    @staticmethod
    def fake(
        analysis_id: str | None = None,
        name: str | None = None,
        account_id: str | None = None,
        status: str = _default_status,
        created_at: str | None = None,
        folder_id: str | None = None,
        is_archived: bool = False,
    ) -> Analysis:
        return Analysis.create(
            AnalysesFaker.fake_dto(
                analysis_id=analysis_id,
                name=name,
                account_id=account_id,
                status=status,
                created_at=created_at,
                folder_id=folder_id,
                is_archived=is_archived,
            )
        )

    @staticmethod
    def fake_dto(
        analysis_id: str | None = None,
        name: str | None = None,
        account_id: str | None = None,
        status: str = _default_status,
        created_at: str | None = None,
        folder_id: str | None = None,
        is_archived: bool = False,
    ) -> AnalysisDto:
        return AnalysisDto(
            id=analysis_id or Id.create().value,
            name=name or AnalysesFaker._faker.sentence(nb_words=4),
            account_id=account_id or Id.create().value,
            status=status,
            created_at=created_at or datetime.now(UTC).isoformat(),
            folder_id=folder_id,
            is_archived=is_archived,
        )

    @staticmethod
    def fake_many(count: int) -> list[Analysis]:
        return [AnalysesFaker.fake() for _ in range(count)]

    @staticmethod
    def fake_many_dto(count: int) -> list[AnalysisDto]:
        return [AnalysesFaker.fake_dto() for _ in range(count)]
