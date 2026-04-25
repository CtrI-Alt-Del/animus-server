from typing import Any, cast

from sentence_transformers import SentenceTransformer

from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.petition_summary_embedding import (
    PetitionSummaryEmbedding,
)
from animus.core.intake.interfaces.petition_embeddings_provider import (
    PetitionSummaryEmbeddingsProvider,
)
from animus.core.shared.domain.structures import Decimal, Text


class BertimbauPetitionSummaryEmbeddingsProvider(PetitionSummaryEmbeddingsProvider):
    _BATCH_SIZE = 64

    def __init__(self) -> None:
        self._model: Any = SentenceTransformer('rufimelo/Legal-BERTimbau-sts-large')

    def generate(
        self,
        petition_summary: PetitionSummary,
    ) -> list[PetitionSummaryEmbedding]:
        texts_to_embed: list[str] = []

        texts_to_embed.append(petition_summary.case_summary.value)
        texts_to_embed.append(petition_summary.legal_issue.value)
        texts_to_embed.append(petition_summary.central_question.value)

        laws = [item.value for item in petition_summary.relevant_laws]
        if laws:
            texts_to_embed.append('Fundamentos normativos: ' + ' | '.join(laws))

        for item in petition_summary.key_facts:
            texts_to_embed.append(item.value)

        for item in petition_summary.search_terms:
            texts_to_embed.append(item.value)

        raw_vectors = self._model.encode(
            texts_to_embed,
            batch_size=self._BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        vectors = cast('list[list[float]]', raw_vectors.tolist())

        return [
            PetitionSummaryEmbedding.create(
                vector=[Decimal.create(float(value)) for value in vector],
                chunk=Text.create(chunk),
            )
            for chunk, vector in zip(texts_to_embed, vectors, strict=True)
        ]
