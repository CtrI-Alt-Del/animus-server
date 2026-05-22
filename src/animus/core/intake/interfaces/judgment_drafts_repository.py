from typing import Protocol


from animus.core.intake.domain.structures import SecondInstanceJudgmentDraft
from animus.core.shared.domain.structures import Id


class SecondInstanceJudgmentDraftsRepository(Protocol):
    def find_by_analysis_id(
        self, analysis_id: Id
    ) -> SecondInstanceJudgmentDraft | None: ...

    def add(self, judgment_draft: SecondInstanceJudgmentDraft) -> None: ...

    def replace(self, judgment_draft: SecondInstanceJudgmentDraft) -> None: ...
