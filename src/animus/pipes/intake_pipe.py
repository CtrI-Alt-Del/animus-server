from typing import Annotated

from fastapi import Depends

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PetitionNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.shared.domain.errors import ForbiddenError
from animus.core.shared.domain.structures import FilePath, Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.validation.shared import IdSchema


class IntakePipe:
    @staticmethod
    def verify_analysis_by_account_from_request(
        analysis_id: IdSchema,
        account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
        analisyses_repository: Annotated[
            AnalisysesRepository,
            Depends(DatabasePipe.get_analisyses_repository_from_request),
        ],
    ) -> Analysis:
        analysis = analisyses_repository.find_by_id(Id.create(analysis_id))
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.account_id.value != account_id.value:
            raise ForbiddenError('Analise nao pertence a conta autenticada')

        return analysis

    @staticmethod
    def verify_petition_document_path_by_account(
        petition_id: IdSchema,
        account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
        petitions_repository: Annotated[
            PetitionsRepository,
            Depends(DatabasePipe.get_petitions_repository_from_request),
        ],
        analisyses_repository: Annotated[
            AnalisysesRepository,
            Depends(DatabasePipe.get_analisyses_repository_from_request),
        ],
    ) -> FilePath:
        petition = petitions_repository.find_by_id(Id.create(petition_id))
        if petition is None:
            raise PetitionNotFoundError

        analysis = analisyses_repository.find_by_id(petition.analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.account_id.value != account_id.value:
            raise ForbiddenError('Peticao nao pertence a conta autenticada')

        return petition.document.file_path
