from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.move_analyses_to_folder_use_case import (
    MoveAnalysesToFolderUseCase,
)
from animus.core.library.domain.errors.folder_not_found_error import (
    FolderNotFoundError,
)
from animus.core.library.interfaces.folders_repository import FoldersRepository
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker
from animus.fakers.library.entities.folders_faker import FoldersFaker


class TestMoveAnalysesToFolderUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.folders_repository_mock = create_autospec(
            FoldersRepository,
            instance=True,
        )
        self.use_case = MoveAnalysesToFolderUseCase(
            analisyses_repository=self.analisyses_repository_mock,
            folders_repository=self.folders_repository_mock,
        )

    def test_should_move_analyses_to_folder_and_persist_them(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        account_id = '01BX5ZZKBKACTAV9WEVGEMMVRZ'
        folder_id = '01BX5ZZKBKACTAV9WEVGEMMVS1'

        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=account_id,
        )
        folder = FoldersFaker.fake(
            folder_id=folder_id,
            account_id=account_id,
        )

        self.analisyses_repository_mock.find_by_id.return_value = analysis
        self.folders_repository_mock.find_by_id.return_value = folder

        result = self.use_case.execute(
            account_id=account_id,
            analysis_ids=[analysis_id],
            folder_id=folder_id,
        )

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.folders_repository_mock.find_by_id.assert_called_once_with(
            Id.create(folder_id)
        )
        self.analisyses_repository_mock.replace.assert_called_once_with(analysis)
        assert result[0].folder_id == folder_id

    def test_should_move_analyses_to_none_folder(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        account_id = '01BX5ZZKBKACTAV9WEVGEMMVRZ'

        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=account_id,
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVS1',
        )

        self.analisyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(
            account_id=account_id,
            analysis_ids=[analysis_id],
            folder_id=None,
        )

        assert result[0].folder_id is None
        self.folders_repository_mock.find_by_id.assert_not_called()

    def test_should_raise_folder_not_found_error_when_folder_belongs_to_another_account(
        self,
    ) -> None:
        account_id = '01BX5ZZKBKACTAV9WEVGEMMVRZ'
        folder_id = '01BX5ZZKBKACTAV9WEVGEMMVS1'

        folder = FoldersFaker.fake(
            folder_id=folder_id,
            account_id='01BX5ZZKBKACTAV9WEVGEMMVS0',
        )

        self.folders_repository_mock.find_by_id.return_value = folder

        with pytest.raises(FolderNotFoundError):
            self.use_case.execute(
                account_id=account_id,
                analysis_ids=['some-id'],
                folder_id=folder_id,
            )

    def test_should_raise_analysis_not_found_error_when_any_analysis_belongs_to_another_account(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        account_id = '01BX5ZZKBKACTAV9WEVGEMMVRZ'

        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id='01BX5ZZKBKACTAV9WEVGEMMVS0',
        )

        self.analisyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                account_id=account_id,
                analysis_ids=[analysis_id],
                folder_id=None,
            )
