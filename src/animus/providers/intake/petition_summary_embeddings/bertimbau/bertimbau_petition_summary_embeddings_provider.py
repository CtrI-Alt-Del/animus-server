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

    _ACCESSORY_MARKERS = (
        'súmula 85',
        'sumula 85',
        '11.960',
        'ipca-e',
        'juros',
        'correção monetária',
        'correcao monetaria',
        'prescrição',
        'prescricao',
        'quinquênio',
        'quinquenio',
        'parcelas vencidas',
        'parcelas vincendas',
        'honorários',
        'honorarios',
        'custas',
    )

    def __init__(self) -> None:
        self._model: Any = SentenceTransformer('rufimelo/Legal-BERTimbau-sts-large')

    def generate(
        self,
        petition_summary: PetitionSummary,
    ) -> list[PetitionSummaryEmbedding]:
        texts_to_embed: list[str] = []

        # 1) Controvérsia central
        texts_to_embed.append(petition_summary.case_summary.value)
        texts_to_embed.append(petition_summary.legal_issue.value)
        texts_to_embed.append(petition_summary.central_question.value)

        # 2) Leis relevantes — todas, sem filtro hardcoded por tokens
        core_laws = [
            item.value
            for item in petition_summary.relevant_laws
            if not self._is_accessory_text(item.value)
        ]
        if core_laws:
            texts_to_embed.append('Fundamentos normativos: ' + ' | '.join(core_laws))

        # 3) Fatos relevantes — exclui apenas acessórios
        for item in petition_summary.key_facts:
            if not self._is_accessory_text(item.value):
                texts_to_embed.append(item.value)

        # 4) Search terms — cada termo vira um chunk individual
        for item in petition_summary.search_terms:
            if not self._is_accessory_text(item.value):
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

    def _is_accessory_text(self, text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in self._ACCESSORY_MARKERS)
