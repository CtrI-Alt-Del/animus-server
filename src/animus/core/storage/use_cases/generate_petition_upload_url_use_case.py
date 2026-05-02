from animus.core.shared.domain.structures import FilePath
from animus.core.shared.domain.structures.id import Id
from animus.core.storage.domain.structures.dtos.upload_url_dto import UploadUrlDto
from animus.core.storage.interfaces.file_storage_provider import FileStorageProvider


class GeneratePetitionUploadUrlUseCase:
    def __init__(self, file_storage_provider: FileStorageProvider) -> None:
        self._file_storage_provider = file_storage_provider

    def execute(self, analysis_id: str, document_type: str) -> UploadUrlDto:
        file_id = Id.create().value
        raw_file_path = (
            f'intake/analyses/{analysis_id}/petitions/{file_id}.{document_type}'
        )
        file_path = FilePath.create(value=raw_file_path)
        upload_url = self._file_storage_provider.generate_upload_url(
            file_path=file_path
        )
        return upload_url.dto
