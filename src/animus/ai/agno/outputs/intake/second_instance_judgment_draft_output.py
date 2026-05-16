from pydantic import BaseModel


class SecondInstanceJudgmentDraftOutput(BaseModel):
    relatorio: str
    fundamentacao: str
    analise_de_aderencia_ou_distincao: str
    dispositivo_sugerido: str
    aviso_ausencia_precedente_aplicavel: str | None = None
