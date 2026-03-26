from typing import Any

import google.genai as genai
from google.genai.types import ContentEmbedding

from animus.constants.env import Env
from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.domain.structures.precedent_embedding_field import PrecedentEmbeddingField
from animus.core.intake.interfaces.precedent_embeddings_provider import (
    PrecedentEmbeddingsProvider,
)
from animus.core.shared.domain.structures.decimal import Decimal
from animus.core.shared.domain.structures.text import Text


class GeminiPrecedentEmbeddingsProvider(PrecedentEmbeddingsProvider):
    def __init__(self, api_key: str | None = None) -> None:
        if api_key:
            self._client = genai.Client(api_key=api_key)
        self._model = Env.EMBEDDING_AI_MODEL

    def generate(self, precedents: list[Precedent]) -> list[PrecedentEmbedding]:
        if not precedents:
            return []
        results: list[PrecedentEmbedding] = []
        texts_to_embed: list[str] = []
        metadata_tracking: list[dict[str, Any]] = []
        for precedent in precedents:
            if precedent.enunciation.value:
                texts_to_embed.append(precedent.enunciation.value)
                metadata_tracking.append(
                    {
                        'precedent': precedent,
                        'field': 'ENUNCIATION',
                        'chunk': precedent.enunciation.value,
                    }
                )
            if precedent.thesis.value:
                texts_to_embed.append(precedent.thesis.value)
                metadata_tracking.append(
                    {
                        'precedent': precedent,
                        'field': 'THESIS',  # Substitua pelo valor correto do seu StrEnum
                        'chunk': precedent.thesis.value,
                    }
                )
        if not texts_to_embed:
            return []
        response = self._client.models.embed_content( # type:ignore
            model=self._model,
            contents=texts_to_embed,
        )
        embeddings: list[ContentEmbedding] = response.embeddings # type:ignore
        for metadata, vector in zip(metadata_tracking, embeddings):
            prec: Precedent = metadata['precedent']
            results.append(
                PrecedentEmbedding.create(
                    score=Decimal.create(1.0), # Score padrão inicial (será recalculado na busca)
                    vector=[Decimal.create(v) for v in vector],
                    field=PrecedentEmbeddingField.create(metadata["field"]),
                    court=prec.identifier.court,
                    number=prec.identifier.number,
                    chunk=Text.create(metadata["chunk"]),
                )
            )
        return results
