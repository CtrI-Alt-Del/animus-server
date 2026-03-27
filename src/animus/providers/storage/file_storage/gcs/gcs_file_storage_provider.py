import os

from google.cloud.storage import Client

from animus.constants import Env
from animus.core.shared.domain.structures import Decimal, Text
from animus.core.storage.domain.structures import File, UploadUrl
from animus.core.storage.interfaces import FileStorageProvider


class GcsFileStorageProvider(FileStorageProvider):
    def __init__(self) -> None:
        storage_emulator_host = Env.STORAGE_EMULATOR_HOST
        if Env.MODE == 'dev' and not storage_emulator_host:
            storage_emulator_host = 'http://localhost:4443'

        if storage_emulator_host:
            os.environ['STORAGE_EMULATOR_HOST'] = storage_emulator_host
            self._client = Client.create_anonymous_client()
        else:
            self._client = Client()

    def generate_upload_url(self, file_path: Text) -> UploadUrl:
        msg = f'generate_upload_url is not implemented for file: {file_path.value}'
        raise NotImplementedError(msg)

    def get_file(self, file_path: Text) -> File:
        bucket = self._client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
        blob = bucket.blob(file_path.value)  # pyright: ignore[reportUnknownMemberType]
        file_content = blob.download_as_bytes()  # pyright: ignore[reportUnknownMemberType]
        size_in_bytes = float(blob.size if blob.size is not None else len(file_content))
        mime_type = (
            blob.content_type
            if blob.content_type is not None
            else 'application/octet-stream'
        )

        return File.create(
            value=file_content,
            key=file_path,
            size_in_bytes=Decimal(value=size_in_bytes),
            mime_type=Text.create(mime_type),
        )
