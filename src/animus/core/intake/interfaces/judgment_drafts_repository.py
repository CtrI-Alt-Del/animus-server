from typing import Protocol

from animus.core.intake.domain.structures.judgment_draft import JudgmentDraft
from animus.core.shared.domain.structures import Id


class JudgmentDraftsRepository(Protocol):
    def find_by_analysis_id(self, analysis_id: Id) -> JudgmentDraft | None: ...

    def add(self, judgment_draft: JudgmentDraft) -> None: ...

    def replace(self, judgment_draft: JudgmentDraft) -> None: ...
