from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import IndexDatapoint

from animus.constants.env import Env
from animus.core.intake.domain.structures.court import Court
from animus.core.intake.domain.structures.petition_embedding import PetitionEmbedding
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.domain.structures.precedent_embedding_field import (
    PrecedentEmbeddingField,
)
from animus.core.intake.interfaces.precedents_embeddings_repository import (
    PrecedentsEmbeddingsRepository,
)
from animus.core.shared.domain.structures.decimal import Decimal
from animus.core.shared.domain.structures.integer import Integer
from animus.core.shared.domain.structures.text import Text
from animus.core.shared.responses.list_response import ListResponse


class VertexAiPrecedentsEmbeddingsRepository(PrecedentsEmbeddingsRepository):
    def __init__(
        self,
    ) -> None:
        aiplatform.init(project=Env.VERTEX_AI_PROJECT, location=Env.VERTEX_AI_LOCATION)
        self._index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            Env.VERTEX_AI_INDEX_ENDPOINT_ID
        )
        self._deployed_index_id = Env.VERTEX_AI_DEPLOY_INDEX_ID

    def find_many(
        self,
        petition_embeddings: list[PetitionEmbedding],
    ) -> ListResponse[PrecedentEmbedding]:
        queries = [
            [float(v.value) for v in p_emb.vector] for p_emb in petition_embeddings
        ]
        response = self._index_endpoint.find_neighbors(  # type: ignore
            deployed_index_id=self._deployed_index_id,
            queries=queries,
            num_neighbors=10,  # Hardcoded por enquanto, alinhado com o tempo que temos.
        )
        results: list[PrecedentEmbedding] = []
        for query_neighbors in response:
            for neighbor in query_neighbors:
                try:
                    court_str, number_str, field_str = neighbor.id.split('::')
                except ValueError:
                    continue

                results.append(
                    PrecedentEmbedding.create(
                        score=Decimal.create(neighbor.distance),  # type:ignore
                        vector=[],
                        field=PrecedentEmbeddingField.create(field_str),
                        court=Court.create(court_str),
                        number=Integer.create(int(number_str)),
                        chunk=Text.create(''),
                    )
                )

        return ListResponse(items=results)

    def add_many(self, precedents_embeddings: list[PrecedentEmbedding]) -> None:
        if not precedents_embeddings:
            return
        datapoints: list[IndexDatapoint] = []
        for emb in precedents_embeddings:
            dp_id = f'{emb.court.dto}::{emb.number.value}::{emb.field.dto}'
            vector_floats = [float(v.value) for v in emb.vector]
            datapoints.append(
                IndexDatapoint(
                    datapoint_id=dp_id,
                    feature_vector=vector_floats,
                )
            )
        self._index_endpoint.upsert_datapoints(  # type: ignore
            deployed_index_id=self._deployed_index_id, datapoints=datapoints
        )
