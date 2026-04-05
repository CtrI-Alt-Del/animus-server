import uuid
from typing import Any, Protocol, TypedDict, cast

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Condition,
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchAny,
    Prefetch,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from animus.constants.env import Env
from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFilters,
)
from animus.core.intake.domain.structures.dtos.precedent_embedding_dto import (
    PrecedentEmbeddingDto,
)
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.petition_summary_embedding import (
    PetitionSummaryEmbedding,
)
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.interfaces.precedents_embeddings_repository import (
    PrecedentsEmbeddingsRepository,
)
from animus.core.shared.domain.structures import Integer
from animus.core.shared.responses.list_response import ListResponse


class _GroupedPoint(TypedDict):
    court: str
    kind: str
    number: int
    vectors: dict[str, list[float]]
    sparse_vectors: dict[str, SparseVector]
    chunks: dict[str, str]


class _SparseEmbeddingLike(Protocol):
    indices: list[int]
    values: list[float]


class QdrantPrecedentsEmbeddingsRepository(PrecedentsEmbeddingsRepository):
    def __init__(self) -> None:
        self._client = QdrantClient(url=Env.QDRANT_URL, api_key=Env.QDRANT_API_KEY)
        self._collection_name = f'{Env.MODE}_precedents'
        self._sparse_model = SparseTextEmbedding(model_name='Qdrant/bm25')
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        if not self._client.collection_exists(collection_name=self._collection_name):
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config={
                    'enunciation': VectorParams(size=3072, distance=Distance.COSINE),
                    'thesis': VectorParams(size=3072, distance=Distance.COSINE),
                },
                sparse_vectors_config={
                    'enunciation_sparse': SparseVectorParams(),
                    'thesis_sparse': SparseVectorParams(),
                },
            )

    def _encode_sparse(self, text: str) -> SparseVector:
        sparse_results = list(self._sparse_model.embed([text]))
        if not sparse_results:
            return SparseVector(indices=[], values=[])

        result = cast(_SparseEmbeddingLike, sparse_results[0])
        return SparseVector(
            indices=[int(index) for index in result.indices],
            values=[float(value) for value in result.values],
        )

    def add_many(self, precedents_embeddings: list[PrecedentEmbedding]) -> None:
        if not precedents_embeddings:
            return

        grouped_points: dict[str, _GroupedPoint] = {}
        for embedding in precedents_embeddings:
            composite_key = (
                f'{embedding.identifier.court.dto}'
                f'::{embedding.identifier.kind.dto}'
                f'::{embedding.identifier.number.value}'
            )

            if composite_key not in grouped_points:
                grouped_points[composite_key] = {
                    'court': embedding.identifier.court.dto,
                    'kind': embedding.identifier.kind.dto,
                    'number': embedding.identifier.number.value,
                    'vectors': {},
                    'sparse_vectors': {},
                    'chunks': {},
                }

            field_name = embedding.field.dto.lower()
            grouped_points[composite_key]['vectors'][field_name] = [
                float(value.value) for value in embedding.vector
            ]
            grouped_points[composite_key]['chunks'][field_name] = embedding.chunk.value

            if embedding.chunk.value:
                grouped_points[composite_key]['sparse_vectors'][
                    f'{field_name}_sparse'
                ] = self._encode_sparse(embedding.chunk.value)

        points: list[PointStruct] = []
        for composite_key, data in grouped_points.items():
            all_vectors: dict[str, Any] = {**data['vectors'], **data['sparse_vectors']}
            points.append(
                PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_OID, composite_key)),
                    vector=all_vectors,
                    payload={
                        'court': data['court'],
                        'kind': data['kind'],
                        'number': data['number'],
                        'chunks': data['chunks'],
                    },
                )
            )

        self._client.upsert(collection_name=self._collection_name, points=points)

    def find_many(
        self,
        petition_summary_embeddings: list[PetitionSummaryEmbedding],
        filters: AnalysisPrecedentsSearchFilters,
        limit: Integer,
    ) -> ListResponse[PrecedentEmbedding]:
        if not petition_summary_embeddings:
            return ListResponse(items=[])

        query_filter = self._build_query_filter(filters)
        results: list[PrecedentEmbedding] = []

        for petition_embedding in petition_summary_embeddings:
            dense_vector = [
                float(decimal.value) for decimal in petition_embedding.vector
            ]
            sparse_vector = self._encode_sparse(petition_embedding.chunk.value)

            for target_field in ('enunciation', 'thesis'):
                query_response = self._client.query_points(
                    collection_name=self._collection_name,
                    prefetch=[
                        Prefetch(
                            query=dense_vector,
                            using=target_field,
                            filter=query_filter,
                            limit=limit.value,
                        ),
                        Prefetch(
                            query=sparse_vector,
                            using=f'{target_field}_sparse',
                            filter=query_filter,
                            limit=limit.value,
                        ),
                    ],
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=limit.value,
                    with_payload=True,
                    with_vectors=False,
                )

                for point in query_response.points:
                    payload = cast('dict[str, object]', point.payload or {})

                    court = payload.get('court')
                    kind = payload.get('kind')
                    number = payload.get('number')
                    if not isinstance(court, str):
                        continue
                    if not isinstance(kind, str):
                        continue
                    if not isinstance(number, int):
                        continue

                    chunk = ''
                    chunks = payload.get('chunks')
                    if isinstance(chunks, dict):
                        chunks_dict = cast('dict[str, object]', chunks)
                        maybe_chunk = chunks_dict.get(target_field)
                        if isinstance(maybe_chunk, str):
                            chunk = maybe_chunk

                    results.append(
                        PrecedentEmbedding.create(
                            PrecedentEmbeddingDto(
                                score=float(point.score),
                                vector=[],
                                field=target_field.upper(),
                                identifier=PrecedentIdentifierDto(
                                    court=court,
                                    kind=kind,
                                    number=number,
                                ),
                                chunk=chunk,
                            )
                        )
                    )

        return ListResponse(items=results)

    @staticmethod
    def _build_query_filter(
        filters: AnalysisPrecedentsSearchFilters,
    ) -> Filter | None:
        conditions: list[Condition] = []

        if filters.courts:
            conditions.append(
                FieldCondition(
                    key='court',
                    match=MatchAny(any=[court.dto for court in filters.courts]),
                )
            )

        if filters.precedent_kinds:
            conditions.append(
                FieldCondition(
                    key='kind',
                    match=MatchAny(
                        any=[
                            precedent_kind.dto
                            for precedent_kind in filters.precedent_kinds
                        ]
                    ),
                )
            )

        if not conditions:
            return None

        return Filter(must=conditions)
