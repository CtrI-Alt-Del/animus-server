from typing import Protocol

from animus.core.shared.domain.structures import FilePath
from animus.core.storage.domain.structures import File, UploadUrl


class FileStorageProvider(Protocol):
    def generate_upload_url(self, file_path: FilePath) -> UploadUrl: ...

    def get_file(self, file_path: FilePath) -> File: ...

    def upload_files(self, file_paths: list[FilePath]) -> None: ...
