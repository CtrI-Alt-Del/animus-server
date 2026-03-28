from typing import Protocol

from animus.core.shared.domain.structures import Text
from animus.core.storage.domain.structures import File, UploadUrl


class FileStorageProvider(Protocol):
    def generate_upload_url(self, file_path: Text) -> UploadUrl: ...

    def get_file(self, file_path: Text) -> File: ...
