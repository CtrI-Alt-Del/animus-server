from __future__ import annotations

from enum import StrEnum


class AnalysisType(StrEnum):
    CASE_ASSESSMENT = 'CASE_ASSESSMENT'
    FIRST_INSTANCE = 'FIRST_INSTANCE'
    SECOND_INSTANCE = 'SECOND_INSTANCE'

    @classmethod
    def normalize(cls, value: str | AnalysisType) -> AnalysisType:
        normalized_value = str(value)
        legacy_mapping = {
            'LAWYER': cls.CASE_ASSESSMENT.value,
            'JUDGE': cls.SECOND_INSTANCE.value,
        }

        return cls(legacy_mapping.get(normalized_value, normalized_value))

    def uses_case_assessment_or_first_instance_flow(self) -> bool:
        return self in {self.CASE_ASSESSMENT, self.FIRST_INSTANCE}
