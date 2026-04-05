from collections.abc import Iterable
from typing import ClassVar, TypedDict

from animus.core.intake.domain.errors import PetitionSummaryUnavailableError
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFilters,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.domain.structures.precedent_embedding_field import (
    PrecedentEmbeddingFieldValue,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.interfaces import (
    PetitionSummariesRepository,
    PetitionSummaryEmbeddingsProvider,
    PrecedentsEmbeddingsRepository,
    PrecedentsRepository,
)
from animus.core.shared.domain.structures import Id, Integer


class _IdentifierScore(TypedDict):
    thesis_max: float
    enunciation_max: float
    thesis_hits: int
    enunciation_hits: int
    total_hits: int


class SearchAnalysisPrecedentsUseCase:
    _GENERIC_NEGATIVE_TERMS: ClassVar[set[str]] = {
        'fgts',
        'urv',
        'imposto de renda',
        'contribuicao previdenciaria',
        'prestacao previdenciaria',
        'insalubridade',
        'periculosidade',
        'ajuda de custo',
        'rescisao indireta',
    }

    _ACCESSORY_MARKERS: ClassVar[set[str]] = {
        'juros',
        'correcao monetaria',
        'correção monetária',
        'honorarios',
        'honorários',
        'custas',
        'prescricao',
        'prescrição',
        'ipca-e',
        'parcelas vencidas',
        'parcelas vincendas',
        'quinquenio',
        'quinquênio',
        'sumula 85',
        'súmula 85',
        '11.960/09',
    }

    _SPECIALIZATION_TERMS: ClassVar[set[str]] = {
        'ferias',
        'férias',
        'aposentadoria',
        'aposentado',
        'aposentado antes',
        'licenca-premio',
        'licença-prêmio',
        'licença premio',
        'conversao em pecunia',
        'conversão em pecúnia',
        'renuncia',
        'renúncia',
        'piso salarial',
        'rsc',
        'retribuicao por titulacao',
        'retribuição por titulação',
        'ferrovia',
    }

    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
        petition_summary_embeddings_provider: PetitionSummaryEmbeddingsProvider,
        precedents_embeddings_repository: PrecedentsEmbeddingsRepository,
        precedents_repository: PrecedentsRepository,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository
        self._petition_summary_embeddings_provider = (
            petition_summary_embeddings_provider
        )
        self._precedents_embeddings_repository = precedents_embeddings_repository
        self._precedents_repository = precedents_repository

    def execute(
        self,
        analysis_id: str,
        dto: AnalysisPrecedentsSearchFiltersDto,
    ) -> list[AnalysisPrecedentDto]:
        analysis_id_entity = Id.create(analysis_id)
        filters = AnalysisPrecedentsSearchFilters.create(dto)

        petition_summary = self._petition_summaries_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if petition_summary is None:
            raise PetitionSummaryUnavailableError

        petition_summary_embeddings = (
            self._petition_summary_embeddings_provider.generate(
                petition_summary,
            )
        )

        candidate_limit = Integer.create(filters.limit.value * 10)
        precedent_embeddings = self._precedents_embeddings_repository.find_many(
            petition_summary_embeddings=petition_summary_embeddings,
            filters=filters,
            limit=candidate_limit,
        )

        if not precedent_embeddings.items:
            return []

        scored_identifiers = self._score_identifiers(precedent_embeddings.items)
        precedents = self._precedents_repository.find_many_by_identifiers(
            identifiers=list(scored_identifiers.keys()),
        )
        precedents_by_identifier = {
            self._get_identifier_key(precedent.identifier): precedent
            for precedent in precedents.items
        }

        analysis_precedents: list[AnalysisPrecedent] = []
        for identifier, scores in scored_identifiers.items():
            precedent = precedents_by_identifier.get(
                self._get_identifier_key(identifier)
            )
            if precedent is None:
                continue

            applicability_percentage = self._calculate_applicability_percentage(
                thesis_score=scores['thesis_max'],
                enunciation_score=scores['enunciation_max'],
                total_hits=scores['total_hits'],
            )

            analysis_precedents.append(
                AnalysisPrecedent.create(
                    AnalysisPrecedentDto(
                        analysis_id=analysis_id_entity.value,
                        precedent=precedent.dto,
                        applicability_percentage=applicability_percentage,
                        synthesis=None,
                        is_chosen=False,
                    )
                )
            )

        sorted_analysis_precedents = sorted(
            analysis_precedents,
            key=lambda item: (
                item.applicability_percentage.value
                if item.applicability_percentage is not None
                else 0.0
            ),
            reverse=True,
        )

        return [item.dto for item in sorted_analysis_precedents[: filters.limit.value]]

    def _score_identifiers(
        self,
        precedent_embeddings: Iterable[PrecedentEmbedding],
    ) -> dict[PrecedentIdentifier, _IdentifierScore]:
        scores_by_identifier: dict[PrecedentIdentifier, _IdentifierScore] = {}

        for precedent_embedding in precedent_embeddings:
            if precedent_embedding.identifier not in scores_by_identifier:
                scores_by_identifier[precedent_embedding.identifier] = {
                    'thesis_max': 0.0,
                    'enunciation_max': 0.0,
                    'thesis_hits': 0,
                    'enunciation_hits': 0,
                    'total_hits': 0,
                }

            score_data = scores_by_identifier[precedent_embedding.identifier]
            score_data['total_hits'] += 1

            field_name = precedent_embedding.field.value
            if field_name is PrecedentEmbeddingFieldValue.THESIS:
                score_data['thesis_max'] = max(
                    score_data['thesis_max'],
                    precedent_embedding.score.value,
                )
                score_data['thesis_hits'] += 1
                continue

            if field_name is PrecedentEmbeddingFieldValue.ENUNCIATION:
                score_data['enunciation_max'] = max(
                    score_data['enunciation_max'],
                    precedent_embedding.score.value,
                )
                score_data['enunciation_hits'] += 1

        return scores_by_identifier

    def _calculate_applicability_percentage(
        self,
        thesis_score: float,
        enunciation_score: float,
        total_hits: int,
    ) -> float:
        base_score = (thesis_score * 0.58) + (enunciation_score * 0.42)
        coverage_bonus = min(total_hits * 0.01, 0.04)

        final_score = base_score + coverage_bonus
        normalized_percentage = round(final_score * 100, 2)

        return min(max(normalized_percentage, 0.0), 95.0)

    def _get_identifier_key(
        self,
        identifier: PrecedentIdentifier,
    ) -> tuple[str, str, int]:
        return (
            identifier.court.dto,
            identifier.kind.dto,
            identifier.number.value,
        )
