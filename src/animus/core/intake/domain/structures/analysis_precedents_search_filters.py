from animus.core.intake.domain.structures.court import Court
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.domain.structures.precedent_kind import PrecedentKind
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Integer


@structure
class AnalysisPrecedentsSearchFilters(Structure):
    courts: list[Court]
    precedent_kinds: list[PrecedentKind]
    limit: Integer

    @classmethod
    def create(
        cls,
        dto: AnalysisPrecedentsSearchFiltersDto,
    ) -> 'AnalysisPrecedentsSearchFilters':
        if dto.limit < 5 or dto.limit > 10:
            raise ValidationError(
                f'Limite deve estar entre 5 e 10, recebido: {dto.limit}'
            )

        return cls(
            courts=cls._normalize_courts(dto.courts),
            precedent_kinds=cls._normalize_precedent_kinds(dto.precedent_kinds),
            limit=Integer.create(dto.limit),
        )

    @staticmethod
    def _normalize_courts(courts: list[str]) -> list[Court]:
        normalized_courts: list[Court] = []
        seen_courts: set[str] = set()

        for court in courts:
            normalized_court = Court.create(court.strip())
            if normalized_court.dto in seen_courts:
                continue

            seen_courts.add(normalized_court.dto)
            normalized_courts.append(normalized_court)

        return normalized_courts

    @staticmethod
    def _normalize_precedent_kinds(precedent_kinds: list[str]) -> list[PrecedentKind]:
        normalized_precedent_kinds: list[PrecedentKind] = []
        seen_precedent_kinds: set[str] = set()

        for precedent_kind in precedent_kinds:
            normalized_precedent_kind = PrecedentKind.create(precedent_kind.strip())
            if normalized_precedent_kind.dto in seen_precedent_kinds:
                continue

            seen_precedent_kinds.add(normalized_precedent_kind.dto)
            normalized_precedent_kinds.append(normalized_precedent_kind)

        return normalized_precedent_kinds

    @property
    def dto(self) -> AnalysisPrecedentsSearchFiltersDto:
        return AnalysisPrecedentsSearchFiltersDto(
            courts=[court.dto for court in self.courts],
            precedent_kinds=[
                precedent_kind.dto for precedent_kind in self.precedent_kinds
            ],
            limit=self.limit.value,
        )
