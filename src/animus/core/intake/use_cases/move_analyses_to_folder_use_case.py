from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.library.domain.errors.folder_not_found_error import (
    FolderNotFoundError,
)
from animus.core.library.interfaces.folders_repository import FoldersRepository
from animus.core.shared.domain.structures import Id


class MoveAnalysesToFolderUseCase:
    def __init__(
        self,
        analisyses_repository: AnalisysesRepository,
        folders_repository: FoldersRepository,
    ) -> None:
        self._analisyses_repository = analisyses_repository
        self._folders_repository = folders_repository

    def execute(
        self,
        account_id: str,
        analysis_ids: list[str],
        folder_id: str | None,
    ) -> list[AnalysisDto]:
        normalized_account_id = Id.create(account_id)
        normalized_folder_id = (
            Id.create(folder_id) if folder_id is not None else None
        )

        if normalized_folder_id is not None:
            folder = self._folders_repository.find_by_id(normalized_folder_id)
            if folder is None or folder.account_id != normalized_account_id:
                raise FolderNotFoundError

        analyses = []
        for analysis_id in analysis_ids:
            normalized_analysis_id = Id.create(analysis_id)
            analysis = self._analisyses_repository.find_by_id(normalized_analysis_id)

            if analysis is None or analysis.account_id != normalized_account_id:
                raise AnalysisNotFoundError

            analyses.append(analysis)

        for analysis in analyses:
            analysis.move_to_folder(normalized_folder_id)
            self._analisyses_repository.replace(analysis)

        return [analysis.dto for analysis in analyses]
