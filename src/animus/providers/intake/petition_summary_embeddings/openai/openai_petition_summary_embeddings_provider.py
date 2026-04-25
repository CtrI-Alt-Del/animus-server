import time

from openai import OpenAI

from animus.constants.env import Env
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.petition_summary_embedding import (
    PetitionSummaryEmbedding,
)
from animus.core.intake.interfaces.petition_embeddings_provider import (
    PetitionSummaryEmbeddingsProvider,
)
from animus.core.shared.domain.structures import Decimal, Text

from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)


petition_summary = PetitionSummary.create(
    PetitionSummaryDto(
        case_summary=(
            'Ação ordinária de cobrança c/c obrigação de fazer proposta por '
            'servidor público federal lotado em município situado em localidade '
            'estratégica de fronteira, visando ao pagamento da indenização de '
            'fronteira prevista na Lei nº 12.855/2013. O autor sustenta que o '
            'Decreto nº 8.216/2014 regulamentou suficientemente a matéria, de modo '
            'que a verba indenizatória é devida automaticamente aos servidores que '
            'preencham os requisitos legais, sem necessidade de ato administrativo '
            'discricionário adicional.'
        ),
        legal_issue=(
            'Exigibilidade da indenização de fronteira prevista na Lei nº 12.855/2013 '
            'a servidor público federal em exercício em localidade estratégica já '
            'abrangida pelo Decreto nº 8.216/2014, diante de omissão administrativa '
            'no pagamento da verba.'
        ),
        central_question=(
            'A Lei nº 12.855/2013, regulamentada pelo Decreto nº 8.216/2014, possui '
            'eficácia suficiente para assegurar o pagamento da indenização de fronteira '
            'aos servidores que preencham os requisitos legais, independentemente de '
            'regulamentação adicional ou de ato administrativo posterior?'
        ),
        relevant_laws=[
            'Lei nº 12.855/2013',
            'Decreto nº 8.216/2014',
            'RR 974',
            'RG 1078',
        ],
        key_facts=[
            'O autor é servidor público federal e exerce suas funções em unidade situada em município reconhecido como região de fronteira.',
            'A Lei nº 12.855/2013 instituiu indenização de R$ 91,00 por jornada de 8 horas aos servidores em localidades estratégicas.',
            'O Decreto nº 8.216/2014 regulamentou as localidades abrangidas e os requisitos formais de operacionalização da verba.',
            'Mesmo preenchendo os requisitos legais desde a vigência da norma, o autor nunca recebeu a indenização.',
            'A inicial sustenta que não há discricionariedade administrativa adicional para concessão da verba.',
            'A ação busca pagamento retroativo das parcelas vencidas no quinquênio anterior e das parcelas vincendas.',
        ],
        search_terms=[
            'RR 974 STJ Lei 12.855/2013 eficácia imediata indenização de fronteira',
            'RG 1078 STF exigibilidade de verba por lotação em unidade estratégica',
            'indenização de fronteira localidade estratégica servidor público federal',
            'Lei 12.855/2013 Decreto 8.216/2014 pagamento automático',
            'omissão administrativa pagamento indenização de fronteira',
            'regulamentação de localidades estratégicas indenização de fronteira',
            'servidor federal lotado em região de fronteira verba indenizatória',
            'cobrança de parcelas vencidas e vincendas indenização de fronteira',
            'exigibilidade da indenização por trabalho em localidade estratégica',
            'necessidade de regulamentação adicional para pagamento da indenização de fronteira',
        ],
        type_of_action='ação ordinária de cobrança c/c obrigação de fazer',
        secondary_legal_issues=[
            'natureza indenizatória da verba de fronteira',
            'alcance temporal da cobrança de parcelas vencidas em relação de trato sucessivo',
            'ausência de discricionariedade administrativa para concessão da indenização',
        ],
        alternative_questions=[
            'A definição das localidades estratégicas pelo Decreto nº 8.216/2014 torna exigível o pagamento da indenização de fronteira?',
            'A natureza indenizatória da verba afasta a necessidade de disponibilidade orçamentária discricionária para sua concessão?',
            'Em ação de cobrança de indenização de fronteira, prescrevem apenas as parcelas anteriores ao quinquênio que antecede o ajuizamento?',
        ],
        jurisdiction_issue=None,
        standing_issue=None,
        requested_relief=[
            'reconhecimento do direito à percepção da indenização de fronteira',
            'pagamento das parcelas vencidas',
            'pagamento das parcelas vincendas',
            'obrigação de fazer consistente na implantação da verba',
        ],
        procedural_issues=[
            'eficácia imediata da Lei nº 12.855/2013 após o Decreto nº 8.216/2014',
            'necessidade ou não de regulamentação adicional para concessão da verba',
            'trato sucessivo no pagamento de vantagem funcional',
        ],
        excluded_or_accessory_topics=[
            'juros de mora',
            'correção monetária pelo IPCA-E',
            'honorários advocatícios',
            'custas processuais',
        ],
    )
)


class OpenAIPetitionSummaryEmbeddingsProvider(PetitionSummaryEmbeddingsProvider):
    _BATCH_SIZE = 10
    _BATCH_DELAY = 6.0

    def __init__(self) -> None:
        self._client = OpenAI(api_key=Env.OPENAI_API_KEY)
        self._model = 'text-embedding-3-large'

    def generate(  # noqa: C901
        self,
        petition_summary: PetitionSummary,
    ) -> list[PetitionSummaryEmbedding]:
        texts_to_embed: list[str] = []
        seen: set[str] = set()

        self._append_unique(
            texts_to_embed,
            seen,
            petition_summary.case_summary.value,
        )

        if petition_summary.type_of_action is not None:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Tipo de ação: {petition_summary.type_of_action.value}',
            )

        self._append_unique(
            texts_to_embed,
            seen,
            f'Questão jurídica principal: {petition_summary.legal_issue.value}',
        )

        self._append_unique(
            texts_to_embed,
            seen,
            f'Pergunta jurídica central: {petition_summary.central_question.value}',
        )

        for item in petition_summary.secondary_legal_issues:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Questão jurídica secundária: {item.value}',
            )

        for item in petition_summary.alternative_questions:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Pergunta jurídica adicional: {item.value}',
            )

        if petition_summary.jurisdiction_issue is not None:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Questão de competência: {petition_summary.jurisdiction_issue.value}',
            )

        if petition_summary.standing_issue is not None:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Questão de legitimidade: {petition_summary.standing_issue.value}',
            )

        laws = [item.value for item in petition_summary.relevant_laws]
        if laws:
            self._append_unique(
                texts_to_embed,
                seen,
                'Fundamentos normativos: ' + ' | '.join(laws),
            )

        for item in petition_summary.key_facts:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Fato relevante: {item.value}',
            )

        for item in petition_summary.requested_relief:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Pedido principal: {item.value}',
            )

        for item in petition_summary.procedural_issues:
            self._append_unique(
                texts_to_embed,
                seen,
                f'Tema processual relevante: {item.value}',
            )

        for item in petition_summary.search_terms:
            self._append_unique(
                texts_to_embed,
                seen,
                item.value,
            )

        structural_chunk = self._build_structural_chunk(petition_summary)
        if structural_chunk is not None:
            self._append_unique(texts_to_embed, seen, structural_chunk)

        procedural_chunk = self._build_procedural_chunk(petition_summary)
        if procedural_chunk is not None:
            self._append_unique(texts_to_embed, seen, procedural_chunk)

        relief_chunk = self._build_relief_chunk(petition_summary)
        if relief_chunk is not None:
            self._append_unique(texts_to_embed, seen, relief_chunk)

        normative_chunk = self._build_normative_chunk(laws)
        if normative_chunk is not None:
            self._append_unique(texts_to_embed, seen, normative_chunk)

        vectors: list[list[float]] = []
        for i in range(0, len(texts_to_embed), self._BATCH_SIZE):
            batch = texts_to_embed[i : i + self._BATCH_SIZE]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            vectors.extend([item.embedding for item in response.data])

            if i + self._BATCH_SIZE < len(texts_to_embed):
                time.sleep(self._BATCH_DELAY)

        return [
            PetitionSummaryEmbedding.create(
                vector=[Decimal.create(float(value)) for value in vector],
                chunk=Text.create(chunk),
            )
            for chunk, vector in zip(texts_to_embed, vectors, strict=True)
        ]

    def _build_structural_chunk(
        self,
        petition_summary: PetitionSummary,
    ) -> str | None:
        parts: list[str] = [
            f'Questão jurídica principal: {petition_summary.legal_issue.value}',
            f'Pergunta jurídica central: {petition_summary.central_question.value}',
        ]

        if petition_summary.type_of_action is not None:
            parts.insert(0, f'Tipo de ação: {petition_summary.type_of_action.value}')

        relevant_secondary = [
            item.value for item in petition_summary.secondary_legal_issues
        ]
        if relevant_secondary:
            parts.append(
                'Questões jurídicas secundárias: ' + ' | '.join(relevant_secondary)
            )

        if petition_summary.jurisdiction_issue is not None:
            parts.append(
                f'Questão de competência: {petition_summary.jurisdiction_issue.value}'
            )

        if petition_summary.standing_issue is not None:
            parts.append(
                f'Questão de legitimidade: {petition_summary.standing_issue.value}'
            )

        return ' || '.join(parts)

    def _build_procedural_chunk(
        self,
        petition_summary: PetitionSummary,
    ) -> str | None:
        issues = [item.value for item in petition_summary.procedural_issues]
        if not issues:
            return None

        return 'Temas processuais e estruturais: ' + ' | '.join(issues)

    def _build_relief_chunk(
        self,
        petition_summary: PetitionSummary,
    ) -> str | None:
        relief = [item.value for item in petition_summary.requested_relief]
        if not relief:
            return None

        return 'Pedidos principais: ' + ' | '.join(relief)

    def _build_normative_chunk(
        self,
        laws: list[str],
    ) -> str | None:
        if not laws:
            return None

        return 'Base normativa principal do caso: ' + ' | '.join(laws)

    def _append_unique(
        self,
        texts_to_embed: list[str],
        seen: set[str],
        text: str | None,
    ) -> None:
        if text is None:
            return

        normalized = ' '.join(text.split()).strip()
        if not normalized:
            return

        lowered = normalized.lower()
        if lowered in seen:
            return

        seen.add(lowered)
        texts_to_embed.append(normalized)
