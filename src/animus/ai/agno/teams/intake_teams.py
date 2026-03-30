from textwrap import dedent

from agno.agent import Agent
from agno.models.google import Gemini

from animus.ai.agno.outputs.intake.petition_summary_output import (
    PetitionSummaryOutput,
)
from animus.constants import Env


class IntakeTeam:
    @property
    def summarize_petition_agent(self) -> Agent:
        return Agent(
            name='Petition Summarizer Agent',
            description='An agent specialized in summarizing legal petitions in PT-BR',
            instructions=dedent(
                """
                Você é um especialista em análise textual de petições judiciais brasileiras.

                Gere um resumo em português brasileiro com saída estruturada contendo:
                - content: visão geral objetiva da petição em linguagem clara;
                - main_points: lista curta com os principais pontos do caso.

                Regras:
                - Seja fiel ao conteúdo recebido, sem inventar informações.
                - Destaque fatos relevantes, fundamento jurídico e pedido principal quando houver.
                - Evite jargão excessivo e texto prolixo.
                - Retorne apenas o objeto estruturado no formato esperado.
                """
            ),
            model=Gemini(id='gemini-2.5-flash', api_key=Env.GEMINI_API_KEY, timeout=60),
            output_schema=PetitionSummaryOutput,
        )
