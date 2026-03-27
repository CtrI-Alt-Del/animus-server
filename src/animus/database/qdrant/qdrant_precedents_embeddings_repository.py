import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, QueryRequest, VectorParams

from animus.core.intake.domain.structures.court import Court
from animus.core.intake.domain.structures.petition_embedding import PetitionEmbedding
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.interfaces.precedents_embeddings_repository import (
    PrecedentsEmbeddingsRepository,
)
from animus.core.shared.domain.structures import Decimal, Integer, Text
from animus.core.shared.responses.list_response import ListResponse


class QdrantPrecedentsEmbeddingsRepository(PrecedentsEmbeddingsRepository):
    def __init__(self, client: QdrantClient, collection_prefix: str) -> None:
        self._client = client
        self._collection_name = f'{collection_prefix}precedents'
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        if not self._client.collection_exists(collection_name=self._collection_name):
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config={
                    'enunciation': VectorParams(size=768, distance=Distance.COSINE),
                    'thesis': VectorParams(size=768, distance=Distance.COSINE),
                },
            )

    def add_many(self, precedents_embeddings: list[PrecedentEmbedding]) -> None:
        if not precedents_embeddings:
            return

        grouped_points = {}
        for emb in precedents_embeddings:
            composite_key = f'{emb.court.dto}::{emb.number.value}'

            if composite_key not in grouped_points:
                grouped_points[composite_key] = {
                    'court': emb.court.dto,
                    'number': emb.number.value,
                    'vectors': {},
                }

            vector_floats = [float(v.value) for v in emb.vector]
            # Converte o nome do campo para minúsculo para bater com a configuração
            field_name = emb.field.dto.lower()
            grouped_points[composite_key]['vectors'][field_name] = vector_floats

        points = []
        for composite_key, data in grouped_points.items():
            point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, composite_key))
            points.append(
                PointStruct(
                    id=point_id,
                    vector=data['vectors'],  # Dicionário com os named vectors
                    payload={
                        'court': data['court'],
                        'number': data['number'],
                    },
                )
            )

        self._client.upsert(collection_name=self._collection_name, points=points)

    def find_many(
        self, petition_embeddings: list[PetitionEmbedding]
    ) -> ListResponse[PrecedentEmbedding]:
        if not petition_embeddings:
            return ListResponse(items=[])

        requests = []
        for p_emb in petition_embeddings:
            target_field = p_emb.field.dto.lower()
            requests.append(
                QueryRequest(
                    query=[float(v.value) for v in p_emb.vector],
                    using=target_field,
                    limit=10,
                    with_payload=True,
                    with_vector=False,  # Economiza banda de rede
                )
            )
        batch_results = self._client.query_batch(
            collection_name=self._collection_name,
            requests=requests,
        )
        results: list[PrecedentEmbedding] = []

        for original_query, query_response in zip(petition_embeddings, batch_results):
            for point in query_response.points:
                payload = point.payload or {}

                results.append(
                    PrecedentEmbedding.create(
                        score=Decimal.create(point.score),
                        vector=[],
                        field=original_query.field,
                        court=Court.create(payload.get('court', '')),
                        number=Integer.create(int(payload.get('number', 0))),
                        chunk=Text.create(''),
                    )
                )

        return ListResponse(items=results)
