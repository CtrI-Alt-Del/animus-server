from textwrap import dedent

from agno.agent import Agent
from agno.models.google import Gemini

from animus.ai.agno.outputs.intake.analysis_precedents_synthesis_output import (
    AnalysisPrecedentsSynthesisOutput,
)
from animus.ai.agno.outputs.intake.petition_summary_output import (
    PetitionSummaryOutput,
)
from animus.constants import Env


class IntakeTeam:
    @property
    def analysis_precedents_synthesizer_agent(self) -> Agent:
        return Agent(
            name='Analysis Precedents Synthesis Agent',
            description='An agent specialized in relating petition summaries to legal precedents in PT-BR',
            instructions=dedent(
                """
                Você é um especialista em correlacionar resumos de petições com precedentes jurídicos brasileiros.

                Receberá um resumo de petição e uma lista de precedentes candidatos.
                Gere uma síntese curta, objetiva e fiel para cada precedente explicando a relação dele com o caso.

                Regras:
                - Seja fiel apenas aos dados fornecidos.
                - Não invente fatos, pedidos, fundamentos ou efeitos jurídicos.
                - Explique a conexão prática entre o precedente e o caso em linguagem clara.
                - Mantenha cada síntese concisa, em português brasileiro, sem markdown.
                - Preserve exatamente `court`, `kind` e `number` recebidos na entrada.
                - Retorne apenas o objeto estruturado no formato esperado.
                """
            ),
            model=Gemini(id='gemini-2.5-flash', api_key=Env.GEMINI_API_KEY, timeout=60),
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
                com foco em extrair uma representação estruturada do caso para busca semântica
                e reranqueamento de precedentes jurídicos aplicáveis.

                Gere uma saída estruturada em português brasileiro contendo:

                - case_summary:
                Resumo objetivo do mérito da petição, com foco no direito pleiteado,
                base legal principal, vínculo jurídico do autor, fato gerador e conduta
                da parte ré. Inclua o nome exato do instituto jurídico central do caso
                (ex: "indenização de fronteira", "tributação fixa do ISS", "violência
                doméstica contra criança", "restituição de valores pagos em consórcio").

                - legal_issue:
                Descreva em uma frase a controvérsia jurídica principal do caso,
                de forma abstrata e juridicamente precisa. Use a terminologia exata
                adotada pelos tribunais superiores para esse tipo de questão.
                Este campo DEVE ser diferente do case_summary — não o repita.

                - central_question:
                Formule a principal pergunta jurídica que um precedente aplicável
                responderia. Use a linguagem dos enunciados de precedentes (IRDRs,
                Temas Repetitivos, IACs, Súmulas), não a linguagem da petição.
                Exemplos de formulação correta:
                - "A Lei nº 12.855/2013 tem eficácia imediata ou depende de
                    regulamentação para definir as localidades estratégicas e autorizar
                    o pagamento da indenização de fronteira?"
                - "As ações penais distribuídas após 30/11/2022 que tratam de crimes
                    com violência contra criança e adolescente devem obrigatoriamente
                    tramitar nos Juizados/Varas de Violência Doméstica?"
                - "O valor da causa em ações de restituição de valores pagos em
                    contratos de consórcio deve corresponder ao proveito econômico
                    pretendido ou ao valor total do contrato?"
                Este campo DEVE ser diferente do case_summary e do legal_issue.

                - relevant_laws:
                Liste apenas leis, decretos, temas repetitivos e precedentes
                diretamente relevantes ao mérito do pedido, sempre com número exato.
                Regras obrigatórias:
                - Sempre inclua o Tema Repetitivo, IRDR ou IAC diretamente aplicável
                    ao mérito do caso, quando identificável pela análise jurídica da
                    petição. Nunca omita o número do precedente principal.
                - Não inclua itens acessórios como Súmula 85 do STJ (prescrição) ou
                    normas de correção monetária, salvo se forem o objeto principal.
                - Nunca retorne lista vazia.

                - key_facts:
                Liste de 3 a 6 fatos juridicamente relevantes e específicos do caso,
                autossuficientes e úteis para busca de precedentes. Cada fato deve
                mencionar o instituto jurídico central do caso e os elementos concretos
                que o caracterizam (ex: data, norma, condição da parte, conduta do réu).

                - search_terms:
                Liste de 8 a 10 expressões curtas e juridicamente específicas, úteis
                como âncoras para busca semântica e lexical de precedentes.

                Regras obrigatórias para os search_terms:
                - O PRIMEIRO search_term deve sempre referenciar o Tema Repetitivo,
                    IRDR ou IAC mais relevante para o caso com seu número exato
                    (ex: "Tema Repetitivo 974 STJ indenização fronteira",
                    "IRDR 77 TJES violência doméstica criança adolescente",
                    "IAC 2 STJ prescrição contrato seguro").
                - Use o vocabulário dos enunciados e teses de precedentes, não o da
                    petição.
                - Inclua o número exato da lei, decreto ou precedente relevante em
                    cada termo que o referencie.
                - Prefira expressões com 3 ou mais palavras para garantir
                    especificidade.
                - Combine o instituto jurídico central com o sujeito ou contexto do
                    caso (ex: "sociedade uniprofissional limitada ISS fixo", "consórcio
                    proveito econômico valor da causa").
                - Inclua pelo menos 2 termos que referenciem diretamente o número do
                    precedente ou lei principal do caso.
                - Não inclua termos acessórios como juros, honorários, correção
                    monetária ou prescrição, salvo se forem o objeto principal.
                - Nunca retorne lista vazia.

                Regras gerais:
                - Seja fiel ao conteúdo recebido, sem inventar informações.
                - Priorize o mérito principal do caso.
                - Os campos case_summary, legal_issue e central_question devem ser
                OBRIGATORIAMENTE diferentes entre si — nunca repita o mesmo texto.
                - Não destaque como núcleo do caso temas acessórios como honorários,
                correção monetária, juros, custas ou prescrição, salvo se forem o
                objeto principal.
                - Sempre que houver base legal específica, inclua seu número exato.
                - Sempre que houver condição funcional, territorial ou normativa especial,
                explicite isso com precisão.
                - Retorne apenas o objeto estruturado no formato esperado.
                """
            ),
            model=Gemini(id='gemini-2.5-flash', api_key=Env.GEMINI_API_KEY, timeout=60),
            output_schema=PetitionSummaryOutput,
        )
