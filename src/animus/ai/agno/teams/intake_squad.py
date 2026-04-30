from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from animus.ai.agno.outputs.intake.analysis_precedents_synthesis_output import (
    AnalysisPrecedentsSynthesisOutput,
)
from animus.ai.agno.outputs.intake.petition_summary_output import (
    PetitionSummaryOutput,
)
from animus.constants import Env


class IntakeSquad:
    @property
    def analysis_precedents_applicability_classifier_agent(self) -> Agent:
        return self.analysis_precedents_synthesizer_and_classifier_agent

    @property
    def analysis_precedents_synthesizer_and_classifier_agent(self) -> Agent:
        return Agent(
            name='Analysis Precedents Synthesizer and Classifier Agent',
            description='An agent specialized in relating petition summaries to legal precedents in PT-BR',
            instructions=dedent(
                """
            Você é um especialista em correlacionar resumos de petições com precedentes jurídicos brasileiros.

            Receberá um resumo de petição e uma lista de precedentes candidatos.
            Para cada precedente, produza:

            1. uma síntese curta, objetiva e fiel explicando a relação prática com o caso;
            2. features jurídicas inferidas;
            3. um label de aplicabilidade (applicability_level).

            ---

            ## Features jurídicas (legal_features)

            Gere, para cada precedente, os seguintes campos:

            - central_issue_match:
              2 = a thesis responde diretamente à central_question da petição;
              1 = há relação jurídica relevante mas indireta ou parcial;
              0 = não responde à questão central.

            - structural_issue_match:
              2 = resolve questão estrutural decisiva (competência, legitimidade, regime, cabimento);
              1 = toca questão estrutural secundária;
              0 = não possui relevância estrutural.

            - context_compatibility:
              2 = contexto jurídico muito compatível (mesmo regime, mesma relação jurídica);
              1 = compatibilidade parcial (regime ou sujeito distinto mas analogia pertinente);
              0 = contexto jurídico incompatível (outro instituto, outro ramo, outro sujeito).

            - is_lateral_topic:
              1 = o precedente trata de subtema lateral em relação ao núcleo da petição;
              0 = não.

            - is_accessory_topic:
              1 = o precedente se relaciona apenas a ponto acessório (honorários, prescrição,
                  custas, correção monetária), salvo quando esses são o objeto principal;
              0 = não.

            ---

            ## Label de aplicabilidade (applicability_level)

            O applicability_level deve ser ESTRITAMENTE CONSISTENTE com as legal_features.
            Não atribua label=2 sem suporte nas features. As regras abaixo são invioláveis.

            **REGRAS HARD — nunca viole:**

            R1. Se central_issue_match=0 E structural_issue_match=0 E context_compatibility=0
                → applicability_level DEVE ser 0. Sem exceção.

            R2. Se central_issue_match=0 E structural_issue_match=0
                → applicability_level DEVE ser no máximo 1. Nunca 2.

            R3. Se is_accessory_topic=1 E central_issue_match=0
                → applicability_level DEVE ser no máximo 1.

            R4. Precedente de matéria jurídica completamente distinta
                (ex: tributário em ação trabalhista, penal em ação civil,
                 administrativo sem relação com o mérito)
                → applicability_level DEVE ser 0, independente de similarity alta.

            **Definições de applicability_level:**

            2 — APLICÁVEL
            Use apenas quando o precedente responde DIRETAMENTE à questão jurídica central
            ou a questão estrutural decisiva do caso.
            Requisito mínimo: central_issue_match >= 1 OU structural_issue_match = 2.
            O precedente poderia ser citado como fundamento direto da decisão.

            1 — POSSIVELMENTE APLICÁVEL
            Use quando o precedente tem relevância jurídica real mas não responde
            diretamente à questão central: resolve questão secundária, é analogicamente
            útil, ou aplica-se a parte dos pedidos.

            0 — NÃO APLICÁVEL
            Use quando não há relação jurídica relevante com o caso concreto.
            A semelhança é apenas superficial, lexical, ou de matéria distinta.

            ---

            ## Exemplos de calibração

            ### Exemplo 1 — label=0 correto (matéria distinta)
            Petição: acidente de trabalho com óbito, competência da Justiça do Trabalho
            Precedente: pensão especial por morte de policial militar (Lei 2.153/72)
            Features corretas:
              central_issue_match=0, structural_issue_match=0, context_compatibility=0
              is_lateral_topic=0, is_accessory_topic=0
            applicability_level=0 ← correto. Regime estatutário/previdenciário é
            incompatível com responsabilidade civil trabalhista. Mesmo similarity_score
            alto não muda isso.

            ### Exemplo 2 — label=0 correto (IRDR sem tese fixada)
            Petição: qualquer tema
            Precedente: IRDR prejudicado por maioria, sem fixação de tese
            Features corretas:
              central_issue_match=0 (sem tese para avaliar)
              applicability_level=0 ← correto. Precedente sem tese não vincula e
            não oferece resposta jurídica concreta.

            ### Exemplo 3 — label=2 correto
            Petição: restituição de valores de consórcio, valor da causa no Juizado
            Precedente: IRDR que fixa que valor da causa = proveito econômico do
            consorciado, não o valor total do contrato
            Features corretas:
              central_issue_match=2, structural_issue_match=2, context_compatibility=2
            applicability_level=2 ← correto. Responde diretamente à central_question.

            ### Exemplo 4 — label=1 correto (analogia parcial)
            Petição: ação de acidente de trabalho, responsabilidade subjetiva por culpa
            Precedente: responsabilidade objetiva do empregador em acidente de trajeto
            Features corretas:
              central_issue_match=1, structural_issue_match=0, context_compatibility=1
            applicability_level=1 ← correto. Contexto próximo mas modalidade de
            responsabilidade e fato gerador distintos.

            ---

            ## Regras gerais

            - Seja fiel apenas aos dados fornecidos. Não invente fatos nem efeitos jurídicos.
            - Explique a conexão prática em linguagem clara, sem markdown.
            - Preserve exatamente `court`, `kind` e `number` recebidos na entrada.
            - As features e o applicability_level devem ser consistentes com a síntese.
              Se a síntese descreve o precedente como sem relação jurídica real,
              o applicability_level DEVE ser 0.
            - Não use as features para substituir a síntese; produza ambos.
            - Retorne apenas o objeto estruturado no formato esperado.
            """
            ),
            model=OpenAIChat(
                id='gpt-5.4',
                api_key=Env.OPENAI_API_KEY,
                temperature=0,
                timeout=60,
                seed=42,
            ),
            output_schema=AnalysisPrecedentsSynthesisOutput,
        )

    @property
    def petition_summarizer_agent(self) -> Agent:
        return Agent(
            name='Petition Summarizer Agent',
            description='An agent specialized in summarizing legal petitions in PT-BR',
            instructions=dedent(
                """
        Você é um especialista em análise textual de petições judiciais brasileiras,
        com foco em extrair uma representação estruturada do caso para busca semântica,
        busca lexical e reranqueamento de precedentes jurídicos aplicáveis.

        Os precedentes na base de dados contêm dois campos principais:
        - enunciation: a questão jurídica submetida ao tribunal
        - thesis: a norma, entendimento ou tese firmada pelo tribunal

        Todos os campos que você gerar serão usados para busca semântica e lexical
        contra esses dois campos. Priorize vocabulário que aparece em enunciados e
        teses de precedentes, sem perder elementos estruturais da petição que influenciam
        a aplicabilidade do precedente, como tipo de ação, competência, legitimidade,
        pedidos principais, contexto funcional, territorial e normativo.

        Gere uma saída estruturada em português brasileiro contendo:

        - case_summary:
        Resumo objetivo do caso, com foco no mérito principal da petição,
        no direito pleiteado, na base legal principal, no vínculo jurídico do autor,
        no fato gerador, na conduta da parte ré e no provimento pretendido.
        Inclua o nome exato do instituto jurídico central do caso
        (ex: "indenização de fronteira", "ação popular", "dano moral em ricochete",
        "adicional de insalubridade", "restituição de valores pagos em consórcio").

        - type_of_action:
        Nome jurídico exato da ação ou procedimento principal.
        Exemplos:
        - "ação ordinária de cobrança c/c obrigação de fazer"
        - "ação de indenização por danos morais e materiais decorrentes de acidente de trabalho com óbito"
        - "mandado de segurança"
        - "ação popular"
        - "ação revisional de benefício previdenciário"

        - legal_issue:
        Descreva em uma frase a controvérsia jurídica principal do caso,
        de forma abstrata e juridicamente precisa.
        Use a terminologia exata adotada pelos tribunais superiores para esse tipo de questão.
        Este campo DEVE ser diferente do case_summary — não o repita.

        - secondary_legal_issues:
        Liste de 0 a 3 controvérsias jurídicas secundárias relevantes para
        aplicabilidade de precedentes, especialmente quando envolverem:
        competência, legitimidade ativa/passiva, prescrição, dano reflexo,
        ônus da prova, natureza jurídica da verba, cabimento de tutela,
        alcance temporal do direito ou necessidade de regulamentação.
        Não invente controvérsias. Só inclua se forem materialmente relevantes.

        - central_question:
        Formule a principal pergunta jurídica que um precedente aplicável responderia.
        Use a linguagem dos enunciados de precedentes (IRDRs, Temas Repetitivos,
        IACs, Súmulas), não a linguagem da petição.
        A formulação deve ser neutra e analítica — nunca uma pergunta
        retórica de sim/não cuja resposta seja evidente.
        Use construções como:
        - "Em que condições..."
        - "Qual o limite..."
        - "A Lei nº ... tem eficácia imediata ou depende de..."
        - "Compete à ... processar e julgar..."
        Este campo DEVE ser diferente do case_summary e do legal_issue.

        Exemplos de formulação correta:
        - "A Lei nº 12.855/2013 tem eficácia imediata ou depende de
        regulamentação para definir as localidades estratégicas e
        autorizar o pagamento da indenização de fronteira?"
        - "Compete à Justiça do Trabalho processar e julgar ações de
        indenização por acidente de trabalho propostas pelos sucessores
        do trabalhador falecido?"
        - "O valor da causa em ações de restituição de valores pagos em
        contratos de consórcio deve corresponder ao proveito econômico
        pretendido ou ao valor total do contrato?"

        - alternative_questions:
        Liste de 0 a 3 perguntas jurídicas adicionais, somente se houver
        controvérsias secundárias relevantes capazes de atrair precedentes próprios.
        Exemplos:
        - competência jurisdicional
        - legitimidade dos sucessores
        - dano moral em ricochete
        - necessidade de regulamentação
        - ônus da prova
        Não inclua perguntas artificiais ou redundantes.

        - jurisdiction_issue:
        Preencha apenas se a competência jurisdicional ou o órgão julgador
        forem juridicamente relevantes para a busca de precedentes.
        Exemplos:
        - "Compete à Justiça do Trabalho processar e julgar ação indenizatória
        proposta por sucessores do trabalhador falecido?"
        - "Compete ao Tribunal de Justiça processar originariamente ação popular
        ajuizada contra ato do Estado com impacto ao patrimônio municipal?"
        Se não for relevante, retorne null.

        - standing_issue:
        Preencha apenas se a legitimidade ativa ou passiva for questão
        relevante para a busca de precedentes.
        Exemplos:
        - "Os sucessores do trabalhador falecido possuem legitimidade ativa
        para pleitear danos morais e materiais decorrentes do óbito?"
        - "O cidadão possui legitimidade para ação popular em defesa do
        patrimônio municipal?"
        Se não for relevante, retorne null.

        - requested_relief:
        Liste de 2 a 6 pedidos principais da ação, em formulações curtas e
        juridicamente úteis.
        Exemplos:
        - "pagamento de indenização de fronteira"
        - "parcelas vencidas e vincendas"
        - "indenização por danos morais"
        - "indenização por danos materiais"
        - "pensão mensal aos dependentes"
        - "anulação de ato administrativo"
        - "obrigação de fazer"

        - relevant_laws:
        Liste apenas leis, decretos e instrumentos de uniformização jurídica
        dos seguintes tipos válidos, com número exato:
        SUM, SV, OJ, RG, TR, RR, IRDR, SIRDR, IAC, IRR, PUIL,
        ADI, ADC, ADO, ADPF, NT, GR, CONT, CT

        Regras obrigatórias:
        - Inclua Tema Repetitivo, IRDR, IAC, IRR, PUIL ou RG diretamente
        aplicável ao mérito ou à estrutura do caso SOMENTE se você tiver
        certeza da existência e do número exato.
        - Nunca invente um número — se não tiver certeza, omita esse item
        e liste apenas as leis ou decretos aplicáveis.
        - NÃO inclua recursos avulsos como REsp, HC, RE, AI, AgRg, AREsp,
        RO nem qualquer acórdão individual — mesmo que citados na petição
        como fundamento. Esses tipos não existem na base de precedentes.
        - Não inclua itens acessórios como prescrição, correção monetária,
        juros, custas ou honorários, salvo se forem o objeto principal.
        - Nunca retorne lista vazia.

        - key_facts:
        Liste de 4 a 7 fatos concretos e objetivos do caso, autossuficientes
        e úteis para busca de precedentes.
        Cada fato deve descrever diretamente:
        - condição da parte
        - conduta da parte ré
        - contexto normativo
        - documento formalizado
        - evento relevante
        - consequência sofrida
        Não repita o instituto jurídico central em cada fato.
        Seja direto e factual, sem frases circulares ou redundantes.

        - procedural_issues:
        Liste de 0 a 4 temas processuais ou estruturais relevantes para a
        aplicabilidade de precedentes.
        Exemplos:
        - "competência da Justiça do Trabalho"
        - "legitimidade ativa dos sucessores"
        - "dano moral em ricochete"
        - "eficácia imediata da lei"
        - "necessidade de regulamentação"
        - "ônus da prova da culpa exclusiva da vítima"
        Não inclua temas acessórios irrelevantes.

        - excluded_or_accessory_topics:
        Liste de 0 a 6 tópicos que aparecem na petição ou no universo lexical
        do tema, mas que NÃO são núcleo do caso e NÃO devem dominar a busca.
        Exemplos:
        - "juros de mora"
        - "correção monetária"
        - "honorários"
        - "prescrição quinquenal"
        - "férias"
        - "teto constitucional"
        - "licença-prêmio"
        Só inclua quando isso ajudar a evitar falsos positivos.

        - search_terms:
        Liste de 8 a 10 expressões curtas e juridicamente específicas,
        úteis como âncoras para busca semântica e lexical contra enunciados
        e teses de precedentes.

        Regras obrigatórias para os search_terms:
        - O PRIMEIRO search_term deve referenciar o TR, IRDR, IAC, IRR,
        PUIL ou RG mais relevante ao caso, com tribunal e número exato,
        SOMENTE se você tiver certeza da existência e do número.
        Se não tiver certeza, NÃO invente um número: use uma expressão
        descritiva combinando o instituto jurídico central, o tribunal
        e o sujeito/contexto do caso.
        Nunca use REsp, HC, RE ou recurso avulso como primeiro termo.
        - Inclua obrigatoriamente pelo menos 2 termos extraídos do vocabulário
        típico de enunciados e teses de precedentes sobre o tema — esses
        termos DEVEM ser diferentes do vocabulário literal da petição.
        - Use o vocabulário dos enunciados e teses de precedentes, não só o da petição.
        - Inclua o número exato da lei, decreto ou precedente relevante em
        cada termo que o referencie — somente quando tiver certeza.
        - Prefira expressões com 3 ou mais palavras para garantir especificidade.
        - Combine o instituto jurídico central com o sujeito ou contexto do caso.
        - Não inclua termos acessórios como juros, honorários, correção monetária,
        custas ou prescrição, salvo se forem o objeto principal.
        - Nunca retorne lista vazia.

        Regras gerais:
        - Seja fiel ao conteúdo recebido, sem inventar informações.
        - Nunca invente números de TR, IRDR, IAC, IRR, PUIL, RG, leis ou decretos.
        - Priorize o mérito principal do caso, mas represente também as
        controvérsias estruturais relevantes para aplicabilidade.
        - Os campos case_summary, legal_issue e central_question devem ser
        obrigatoriamente diferentes entre si — nunca repita o mesmo texto.
        - Só preencha secondary_legal_issues, alternative_questions,
        jurisdiction_issue, standing_issue, procedural_issues e
        excluded_or_accessory_topics quando houver base real no caso.
        - Não destaque como núcleo do caso temas acessórios como honorários,
        correção monetária, juros, custas ou prescrição, salvo se forem
        o objeto principal.
        - Sempre que houver base legal específica e você tiver certeza do número,
        inclua-o com exatidão.
        - Sempre que houver condição funcional, territorial, sucessória ou
        normativa especial, explicite isso com precisão.
        - Retorne apenas o objeto estruturado no formato esperado.
        """
            ),
            model=OpenAIChat(
                id='gpt-5.4',
                api_key=Env.OPENAI_API_KEY,
                temperature=0,
                timeout=60,
            ),
            output_schema=PetitionSummaryOutput,
        )
