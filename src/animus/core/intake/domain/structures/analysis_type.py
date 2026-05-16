from __future__ import annotations

from enum import StrEnum

from pydantic import ValidationError

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Logical


class AnalysisTypeValue(StrEnum):
    CASE_ASSESSMENT = 'CASE_ASSESSMENT'
    FIRST_INSTANCE = 'FIRST_INSTANCE'
    SECOND_INSTANCE = 'SECOND_INSTANCE'


@structure
class AnalysisType(Structure):
    value: AnalysisTypeValue

    @classmethod
    def create(cls, value: str) -> AnalysisType:
        try:
            return cls(AnalysisTypeValue(value.upper()))
        except ValueError as error:
            raise ValidationError(f'Tipo de precedente invalido: {value}') from error

    @classmethod
    def normalize(cls, value: str) -> AnalysisType:
        return cls.create(value)

    @classmethod
    def create_as_case_assessment(cls) -> AnalysisType:
        return cls(AnalysisTypeValue.CASE_ASSESSMENT)

    @classmethod
    def create_as_first_instance(cls) -> AnalysisType:
        return cls(AnalysisTypeValue.FIRST_INSTANCE)

    @classmethod
    def create_as_second_instance(cls) -> AnalysisType:
        return cls(AnalysisTypeValue.SECOND_INSTANCE)

    @property
    def is_case_analysis(self) -> Logical:
        return Logical.create(self.value == AnalysisTypeValue.CASE_ASSESSMENT)

    @property
    def is_first_instance(self) -> Logical:
        return Logical.create(self.value == AnalysisTypeValue.FIRST_INSTANCE)

    @property
    def is_second_instance(self) -> Logical:
        return Logical.create(self.value == AnalysisTypeValue.SECOND_INSTANCE)

    @property
    def dto(self) -> str:
        return self.value.value
