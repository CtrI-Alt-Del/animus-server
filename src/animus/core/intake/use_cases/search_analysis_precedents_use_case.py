import math
from collections.abc import Iterable
from typing import TypedDict

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

# Pesos da fórmula de scoring.
# thesis recebe maior peso por ser a declaração normativa definitiva do precedente.
# Para precedentes sem thesis (SVs, súmulas), o peso é redistribuído —
# ver _calculate_similarity_score.
_THESIS_WEIGHT: float = 0.50
_ENUNCIATION_WEIGHT: float = 0.50

# Bônus de cobertura: recompensa precedentes que aparecem em muitos chunks da petição.
# Escala logarítmica para discriminar alta cobertura (50 hits) de cobertura básica
# (4 hits) sem inflar o score de precedentes com poucos hits.
# Fórmula: min(log(1 + total_hits) * factor, cap).
# Exemplos: hits=4 → ~2.8%, hits=10 → ~4.8%, hits=20 → ~6.2%, hits=50 → ~8.0%
_COVERAGE_LOG_FACTOR: float = 0.02
_MAX_COVERAGE_BONUS: float = 0.08


class _IdentifierScore(TypedDict):
    thesis_max: float
    enunciation_max: float
    thesis_hits: int
    enunciation_hits: int
    total_hits: int


class SearchAnalysisPrecedentsUseCase:
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

        # Monta lista de (score, scores_dict, identifier_key) para ordenação.
        # O identifier_key é calculado uma única vez aqui e reutilizado no loop
        # de construção dos DTOs, evitando chamadas duplicadas a _get_identifier_key.
        scored_precedents: list[
            tuple[float, _IdentifierScore, tuple[str, str, int]]
        ] = []
        for identifier, scores in scored_identifiers.items():
            identifier_key = self._get_identifier_key(identifier)
            if identifier_key not in precedents_by_identifier:
                continue

            # Score bruto sem cap — preserva ordenação real para o banco e para o ML.
            # O cap de 95% é responsabilidade da camada de serialização REST,
            # não deste use case. Aplicar o cap aqui colapsaria precedentes com
            # scores distintos no mesmo valor, corrompendo a ordenação persistida
            # no banco e os dados de treino do ML.
            similarity_score = self._calculate_similarity_score(
                thesis_score=scores['thesis_max'],
                enunciation_score=scores['enunciation_max'],
                total_hits=scores['total_hits'],
                thesis_hits=scores['thesis_hits'],
                enunciation_hits=scores['enunciation_hits'],
            )

            scored_precedents.append((similarity_score, scores, identifier_key))

        scored_precedents.sort(key=lambda item: item[0], reverse=True)

        analysis_precedents = [
            AnalysisPrecedent.create(
                AnalysisPrecedentDto(
                    analysis_id=analysis_id_entity.value,
                    precedent=precedents_by_identifier[identifier_key].dto,
                    similarity_score=similarity_score,
                    synthesis=None,
                    is_chosen=False,
                    thesis_similarity_score=scores['thesis_max'],
                    enunciation_similarity_score=scores['enunciation_max'],
                    total_search_hits=scores['total_hits'],
                    similarity_rank=rank,
                    applicability_level=None,
                    legal_features=None,
                )
            )
            for rank, (similarity_score, scores, identifier_key) in enumerate(
                scored_precedents, start=1
            )
        ]

        return [item.dto for item in analysis_precedents[: filters.limit.value * 2]]

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

    def _calculate_similarity_score(
        self,
        thesis_score: float,
        enunciation_score: float,
        total_hits: int,
        thesis_hits: int,
        enunciation_hits: int,
    ) -> float:
        """Retorna o score bruto sem cap.

        Ponderação adaptativa por disponibilidade de campos:
        - Ambos ausentes: score zero (precedente sem texto indexado).
        - Apenas enunciation (SVs, súmulas, precedentes em fase inicial):
          usa enunciation com peso total para não penalizar estruturalmente
          precedentes com thesis vazia.
        - Apenas thesis: caso simétrico, usa thesis com peso total.
        - Ambos presentes: ponderação padrão thesis/enunciation.

        Bônus de cobertura em escala logarítmica para discriminar precedentes
        com alta cobertura (50+ hits) de cobertura básica (4 hits) sem inflar
        o score de precedentes com poucos hits.

        O cap de 95% é responsabilidade da camada de serialização REST.
        """
        if thesis_hits == 0 and enunciation_hits == 0:
            base_score = 0.0
        elif thesis_hits == 0:
            base_score = enunciation_score
        elif enunciation_hits == 0:
            base_score = thesis_score
        else:
            base_score = (thesis_score * _THESIS_WEIGHT) + (
                enunciation_score * _ENUNCIATION_WEIGHT
            )

        coverage_bonus = min(
            math.log1p(total_hits) * _COVERAGE_LOG_FACTOR,
            _MAX_COVERAGE_BONUS,
        )

        return round((base_score + coverage_bonus) * 100, 2)

    def _get_identifier_key(
        self,
        identifier: PrecedentIdentifier,
    ) -> tuple[str, str, int]:
        return (
            identifier.court.dto,
            identifier.kind.dto,
            identifier.number.value,
        )
