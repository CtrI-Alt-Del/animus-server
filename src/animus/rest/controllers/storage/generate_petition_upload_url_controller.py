from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.storage.domain.structures.dtos.upload_url_dto import UploadUrlDto
from animus.core.storage.interfaces.file_storage_provider import FileStorageProvider
from animus.core.storage.use_cases.generate_petition_upload_url_use_case import (
    GeneratePetitionUploadUrlUseCase,
)
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.providers_pipe import ProvidersPipe


class GeneratePetitionUploadUrlController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/petitions/upload',
            status_code=201,
        )
        def _(
            analysis_id: str,
            document_type: Annotated[Literal['pdf', 'docx'], Query(...)],
            _guard: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            file_storage_provider: Annotated[
                FileStorageProvider,
                Depends(ProvidersPipe.get_file_storage_provider),
            ],
        ) -> UploadUrlDto:
            use_case = GeneratePetitionUploadUrlUseCase(
                file_storage_provider=file_storage_provider
            )
            return use_case.execute(
                analysis_id=analysis_id,
                document_type=document_type,
            )
