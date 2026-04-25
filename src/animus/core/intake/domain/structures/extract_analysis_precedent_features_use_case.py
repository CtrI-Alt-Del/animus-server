import re
import unicodedata
from dataclasses import dataclass

from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.entities.precedent import Precedent


@dataclass(frozen=True)
class AnalysisPrecedentFeaturesDto:
    same_law_count: int
    same_decree_count: int
    type_of_action_match: int
    requested_relief_overlap_count: int
    has_regime_mismatch: int
    has_specialization_mismatch: int
    has_accessory_topic_overlap: int
    jurisdiction_match: int
    standing_match: int


class ExtractAnalysisPrecedentFeaturesUseCase:
    _LAW_RE = re.compile(
        r'\blei\s*(?:complementar\s*)?(?:n\s*)?(\d+(?:\.\d+)?/\d{2,4})\b',
        re.I,
    )
    _DECREE_RE = re.compile(
        r'\bdecreto\s*(?:n\s*)?(\d+(?:\.\d+)?/\d{2,4})\b',
        re.I,
    )

    _ACTION_TYPE_TERMS = {
        'acao_indenizacao': [
            'acao de indenizacao',
            'danos morais',
            'danos materiais',
            'acidente de trabalho',
        ],
        'acao_cobranca_obrigacao_fazer': [
            'acao ordinaria de cobranca',
            'obrigacao de fazer',
            'parcelas vencidas',
            'parcelas vincendas',
        ],
        'acao_popular': [
            'acao popular',
            'patrimonio publico',
            'moralidade administrativa',
        ],
        'mandado_seguranca': [
            'mandado de seguranca',
            'direito liquido e certo',
        ],
    }

    _RELIEF_SYNONYMS = {
        'indenizacao_danos_morais': [
            'indenizacao por danos morais',
            'dano moral',
            'danos morais',
            'dano moral em ricochete',
            'dano moral reflexo',
            'reparacao moral',
        ],
        'indenizacao_danos_materiais': [
            'indenizacao por danos materiais',
            'dano material',
            'danos materiais',
            'reparacao material',
            'ressarcimento material',
        ],
        'pensao_mensal': [
            'pensao mensal',
            'pensionamento',
            'pensionamento mensal',
            'pensionamento vitalicio',
            'pensionamento aos dependentes',
        ],
        'despesas_funerarias': [
            'reembolso de despesas funerarias',
            'despesas de funeral',
            'funeral',
            'despesas com funeral',
        ],
        'obrigacao_fazer': [
            'obrigacao de fazer',
            'implantacao da verba',
            'implementacao da verba',
            'implantacao da indenizacao',
        ],
        'parcelas_vencidas_vincendas': [
            'parcelas vencidas',
            'parcelas vincendas',
            'pagamento retroativo',
            'pagamento das parcelas vencidas',
            'pagamento das parcelas vincendas',
        ],
    }

    _REGIME_GROUPS = {
        'clt_privado': [
            'empregado',
            'empregador',
            'relacao de trabalho',
            'clt',
            'pessoa juridica de direito privado',
            'empregadora',
            'empresa',
            'trabalhador',
            'reclamante',
            'reclamada',
        ],
        'servidor_estatutario': [
            'servidor estatutario',
            'regime estatutario',
            'administracao publica',
            'administracao publica municipal',
            'municipal',
            'uniao federal',
            'estado',
            'municipio',
            'servidor publico',
            'cargo efetivo',
            'carreira publica',
            'funcionalismo publico',
        ],
    }

    _SPECIALIZATION_GROUPS = {
        'ferias': [
            'ferias',
            'gozo de ferias',
            'ferias regulamentares',
        ],
        'acidente_trajeto': [
            'acidente de trajeto',
            'transporte ao empregado',
            'transporte fornecido',
            'trajeto residencia-trabalho',
        ],
        'licenca_premio': [
            'licenca-premio',
            'licenca premio',
            'licencas-premio',
            'licencas premio',
        ],
        'aposentadoria': [
            'aposentadoria',
            'aposentado',
            'beneficio previdenciario',
            'pensao por morte',
            'revisao de aposentadoria',
        ],
        'localidade_estrategica': [
            'localidade estrategica',
            'localidades estrategicas',
            'indenizacao de fronteira',
            'adicional de fronteira',
            'lei 12.855/2013',
            'decreto 8.216/2014',
            'regiao de fronteira',
            'municipio de fronteira',
        ],
        'acidente_trabalho_fatal': [
            'acidente de trabalho',
            'acidente do trabalho',
            'acidente laboral',
            'empregado morto',
            'vitima fatal',
            'morte do empregado',
            'trabalhador falecido',
            'dano moral em ricochete',
            'dano reflexo',
            'dependentes do trabalhador falecido',
        ],
    }

    _ACCESSORY_TOPICS = {
        'juros': [
            'juros',
            'juros de mora',
        ],
        'correcao_monetaria': [
            'correcao monetaria',
            'ipca-e',
            'atualizacao monetaria',
        ],
        'honorarios': [
            'honorarios',
            'honorarios advocaticios',
            'sucumbencia',
        ],
        'custas': [
            'custas',
            'custas processuais',
        ],
        'prescricao': [
            'prescricao',
            'quinquenio',
            'trato sucessivo',
            'parcelas vencidas',
            'parcelas vincendas',
            'sumula 85',
        ],
        'ferias': [
            'ferias',
            'gozo de ferias',
            'ferias regulamentares',
        ],
        'teto_constitucional': [
            'teto constitucional',
        ],
        'licenca_premio': [
            'licenca-premio',
            'licenca premio',
        ],
    }

    _JURISDICTION_GROUPS = {
        'justica_trabalho': [
            'justica do trabalho',
            'competencia da justica do trabalho',
            'art. 114',
            'artigo 114',
            'trabalhista',
            'vara do trabalho',
        ],
        'justica_federal': [
            'justica federal',
            'vara federal',
            'subsecao judiciaria',
            'secao judiciaria',
            'juiz federal',
        ],
        'tribunal_justica_originaria': [
            'tribunal de justica',
            'competencia originaria',
            'tribunal pleno',
            'tribunal de justica estadual',
        ],
    }

    _STANDING_GROUPS = {
        'sucessores_dependentes': [
            'sucessores',
            'dependentes',
            'dependentes economicos',
            'herdeiros',
            'trabalhador falecido',
            'sucessores do trabalhador falecido',
            'familiares da vitima',
            'nucleo familiar',
        ],
        'servidor_publico': [
            'servidor publico',
            'funcionalismo publico',
            'cargo efetivo',
            'servidor federal',
            'servidor municipal',
        ],
        'cidadao_acao_popular': [
            'cidadao',
            'acao popular',
            'patrimonio publico',
            'autor popular',
        ],
        'pensionistas_herdeiros': [
            'pensionistas',
            'pensao por morte',
            'herdeiros',
            'beneficiarios',
        ],
    }

    def execute(
        self,
        petition_summary: PetitionSummary,
        precedent: Precedent,
    ) -> AnalysisPrecedentFeaturesDto:
        return AnalysisPrecedentFeaturesDto(
            same_law_count=self._same_law_count(petition_summary, precedent),
            same_decree_count=self._same_decree_count(petition_summary, precedent),
            type_of_action_match=self._type_of_action_match(
                petition_summary,
                precedent,
            ),
            requested_relief_overlap_count=self._requested_relief_overlap_count(
                petition_summary,
                precedent,
            ),
            has_regime_mismatch=self._has_regime_mismatch(
                petition_summary,
                precedent,
            ),
            has_specialization_mismatch=self._has_specialization_mismatch(
                petition_summary,
                precedent,
            ),
            has_accessory_topic_overlap=self._has_accessory_topic_overlap(
                petition_summary,
                precedent,
            ),
            jurisdiction_match=self._jurisdiction_match(
                petition_summary,
                precedent,
            ),
            standing_match=self._standing_match(
                petition_summary,
                precedent,
            ),
        )

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = ''.join(
            c
            for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        text = text.replace('nº', 'n').replace('n°', 'n').replace(' nº ', ' n ')
        text = re.sub(r'\s+', ' ', text)
        return text

    def _join_summary_texts(self, summary: PetitionSummary) -> str:
        parts: list[str] = [
            summary.case_summary.value,
            summary.legal_issue.value,
            summary.central_question.value,
            summary.type_of_action.value if summary.type_of_action is not None else '',
            *[item.value for item in summary.relevant_laws],
            *[item.value for item in summary.key_facts],
            *[item.value for item in summary.search_terms],
            *[item.value for item in summary.secondary_legal_issues],
            *[item.value for item in summary.alternative_questions],
            summary.jurisdiction_issue.value
            if summary.jurisdiction_issue is not None
            else '',
            summary.standing_issue.value if summary.standing_issue is not None else '',
            *[item.value for item in summary.requested_relief],
            *[item.value for item in summary.procedural_issues],
            *[item.value for item in summary.excluded_or_accessory_topics],
        ]
        return self._normalize(' | '.join(parts))

    def _join_precedent_texts(self, precedent: Precedent) -> str:
        return self._normalize(
            f'{precedent.enunciation.value} | {precedent.thesis.value}'
        )

    def _extract_laws(self, text: str) -> set[str]:
        return {m.group(1) for m in self._LAW_RE.finditer(self._normalize(text))}

    def _extract_decrees(self, text: str) -> set[str]:
        return {m.group(1) for m in self._DECREE_RE.finditer(self._normalize(text))}

    def _same_law_count(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        summary_laws = self._extract_laws(self._join_summary_texts(summary))
        precedent_laws = self._extract_laws(self._join_precedent_texts(precedent))
        return len(summary_laws & precedent_laws)

    def _same_decree_count(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        summary_decrees = self._extract_decrees(self._join_summary_texts(summary))
        precedent_decrees = self._extract_decrees(self._join_precedent_texts(precedent))
        return len(summary_decrees & precedent_decrees)

    def _detect_action_group(self, text: str) -> str | None:
        text = self._normalize(text)
        best_group = None
        best_hits = 0

        for group, terms in self._ACTION_TYPE_TERMS.items():
            hits = sum(term in text for term in terms)
            if hits > best_hits:
                best_group = group
                best_hits = hits

        return best_group if best_hits > 0 else None

    def _type_of_action_match(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        summary_base = (
            summary.type_of_action.value
            if summary.type_of_action is not None
            else summary.case_summary.value
        )
        summary_group = self._detect_action_group(summary_base)
        precedent_group = self._detect_action_group(
            self._join_precedent_texts(precedent)
        )
        return int(summary_group is not None and summary_group == precedent_group)

    def _detect_relief_groups(self, texts: list[str]) -> set[str]:
        text = self._normalize(' | '.join(texts))
        found: set[str] = set()
        for group, terms in self._RELIEF_SYNONYMS.items():
            if any(term in text for term in terms):
                found.add(group)
        return found

    def _requested_relief_overlap_count(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        summary_groups = self._detect_relief_groups(
            [item.value for item in summary.requested_relief]
        )
        precedent_groups = self._detect_relief_groups(
            [precedent.enunciation.value, precedent.thesis.value]
        )
        return len(summary_groups & precedent_groups)

    def _detect_regime_group(self, text: str) -> str | None:
        text = self._normalize(text)
        best_group = None
        best_hits = 0

        for group, terms in self._REGIME_GROUPS.items():
            hits = sum(term in text for term in terms)
            if hits > best_hits:
                best_group = group
                best_hits = hits

        return best_group if best_hits > 0 else None

    def _has_regime_mismatch(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        summary_group = self._detect_regime_group(self._join_summary_texts(summary))
        precedent_group = self._detect_regime_group(
            self._join_precedent_texts(precedent)
        )

        if summary_group is None or precedent_group is None:
            return 0

        return int(summary_group != precedent_group)

    def _detect_specialization_groups(self, text: str) -> set[str]:
        text = self._normalize(text)
        found: set[str] = set()
        for group, terms in self._SPECIALIZATION_GROUPS.items():
            if any(term in text for term in terms):
                found.add(group)
        return found

    def _has_specialization_mismatch(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        summary_groups = self._detect_specialization_groups(
            self._join_summary_texts(summary)
        )
        precedent_groups = self._detect_specialization_groups(
            self._join_precedent_texts(precedent)
        )

        if not precedent_groups:
            return 0

        unmatched = precedent_groups - summary_groups
        return int(len(unmatched) > 0)

    def _detect_accessory_groups_from_summary(
        self,
        summary: PetitionSummary,
    ) -> set[str]:
        text = self._normalize(
            ' | '.join(item.value for item in summary.excluded_or_accessory_topics)
        )
        found: set[str] = set()
        for group, terms in self._ACCESSORY_TOPICS.items():
            if any(term in text for term in terms):
                found.add(group)
        return found

    def _detect_accessory_groups_from_precedent(
        self,
        precedent: Precedent,
    ) -> set[str]:
        text = self._join_precedent_texts(precedent)
        found: set[str] = set()
        for group, terms in self._ACCESSORY_TOPICS.items():
            if any(term in text for term in terms):
                found.add(group)
        return found

    def _has_accessory_topic_overlap(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        summary_accessories = self._detect_accessory_groups_from_summary(summary)
        precedent_accessories = self._detect_accessory_groups_from_precedent(precedent)
        return int(len(summary_accessories & precedent_accessories) > 0)

    def _detect_group_match(
        self,
        summary_text: str,
        precedent_text: str,
        groups: dict[str, list[str]],
    ) -> int:
        for _, terms in groups.items():
            summary_has = any(term in summary_text for term in terms)
            precedent_has = any(term in precedent_text for term in terms)
            if summary_has and precedent_has:
                return 1
        return 0

    def _jurisdiction_match(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        if summary.jurisdiction_issue is None:
            return 0

        summary_text = self._normalize(summary.jurisdiction_issue.value)
        precedent_text = self._join_precedent_texts(precedent)

        return self._detect_group_match(
            summary_text,
            precedent_text,
            self._JURISDICTION_GROUPS,
        )

    def _standing_match(
        self,
        summary: PetitionSummary,
        precedent: Precedent,
    ) -> int:
        if summary.standing_issue is None:
            return 0

        summary_text = self._normalize(summary.standing_issue.value)
        precedent_text = self._join_precedent_texts(precedent)

        return self._detect_group_match(
            summary_text,
            precedent_text,
            self._STANDING_GROUPS,
        )
