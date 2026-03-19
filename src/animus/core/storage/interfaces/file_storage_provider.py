from typing import Protocol

from animus.core.shared.domain.structures import Text
from animus.core.storage.domain.structures import UploadUrl


class FileStorageProvider(Protocol):
    def generate_upload_url(self, file_path: Text) -> UploadUrl: ...
