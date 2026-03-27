from dataclasses import field
from typing import Any

from animus.core.shared.domain.abstracts.structure import Structure
from animus.core.shared.domain.decorators.structure import structure


@structure
class PangeaBnpParadigmProcess(Structure):
    numero: str = ""
    link: str | None = None

    @classmethod
    def create(cls, **data: Any) -> 'PangeaBnpParadigmProcess':
        return cls(numero=str(data.get('numero', '')), link=data.get('link'))


@structure
class PangeaBnpHighlight(Structure):

    tese: str | None = None
    tese_snippet: str | None = None

    @classmethod
    def create(cls, **data: Any) -> 'PangeaBnpHighlight':
        return cls(tese=data.get('tese'), tese_snippet=data.get('tese_snippet'))


@structure
class PangeaBnpPrecedentProcess(Structure):
    id: str = ""
    nr: int = 0
    orgao: str = ""
    tipo: str = ""
    questao: str = ""
    situacao: str = ""
    ultima_atualizacao: str | None = None
    numero_tema: int | None = None
    tese: str | None = None
    highlight: PangeaBnpHighlight | None = None
    processos_paradigma: list[PangeaBnpParadigmProcess] = field(default_factory=list) # type:ignore

    @classmethod
    def create(cls, **data: Any) -> 'PangeaBnpPrecedentProcess':
        highlight_data = data.get('highlight')
        return cls(
            id=str(data.get('id', '')),
            nr=int(data.get('nr', 0)),
            orgao=str(data.get('orgao', '')),
            tipo=str(data.get('tipo', '')),
            questao=str(data.get('questao', '')),
            situacao=str(data.get('situacao', '')),
            ultima_atualizacao=data.get('ultimaAtualizacao'),
            numero_tema=data.get('numeroTemaSobrestado'),
            tese=data.get('tese'),
            highlight=PangeaBnpHighlight.create(**highlight_data)
            if highlight_data
            else None,
            processos_paradigma=[
                PangeaBnpParadigmProcess.create(**p)
                for p in data.get('processosParadigma', [])
            ],
        )
