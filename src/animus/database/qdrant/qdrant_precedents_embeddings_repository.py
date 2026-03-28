import uuid
from typing import Any, TypedDict, cast

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from animus.constants.env import Env
from animus.core.intake.domain.structures.dtos.precedent_embedding_dto import (
    PrecedentEmbeddingDto,
)
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.petition_embedding import PetitionEmbedding
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.interfaces.precedents_embeddings_repository import (
    PrecedentsEmbeddingsRepository,
)
from animus.core.shared.responses.list_response import ListResponse


class _GroupedPoint(TypedDict):
    court: str
    kind: str
    number: int
    vectors: dict[str, list[float]]
    chunks: dict[str, str]


class QdrantPrecedentsEmbeddingsRepository(PrecedentsEmbeddingsRepository):
    def __init__(self) -> None:
        self._client = QdrantClient(url=Env.QDRANT_URL)
        self._collection_name = f'{Env.MODE}_precedents'
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        if not self._client.collection_exists(collection_name=self._collection_name):
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config={
                    'enunciation': VectorParams(size=1024, distance=Distance.COSINE),
                    'thesis': VectorParams(size=1024, distance=Distance.COSINE),
                },
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
                    'chunks': {},
                }

            field_name = embedding.field.dto.lower()
            grouped_points[composite_key]['vectors'][field_name] = [
                float(value.value) for value in embedding.vector
            ]
            grouped_points[composite_key]['chunks'][field_name] = embedding.chunk.value

        points: list[PointStruct] = []
        for composite_key, data in grouped_points.items():
            points.append(
                PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_OID, composite_key)),
                    vector=cast('dict[str, Any]', data['vectors']),
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
        self, petition_embeddings: list[PetitionEmbedding]
    ) -> ListResponse[PrecedentEmbedding]:
        if not petition_embeddings:
            return ListResponse(items=[])

        results: list[PrecedentEmbedding] = []
        for petition_embedding in petition_embeddings:
            query_vector = [float(value.value) for value in petition_embedding.vector]

            for target_field in ('enunciation', 'thesis'):
                query_response = self._client.query_points(
                    collection_name=self._collection_name,
                    query=query_vector,
                    using=target_field,
                    limit=10,
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
