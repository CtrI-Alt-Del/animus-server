from pathlib import Path

from google.cloud.storage import Client

from animus.constants import Env
from animus.core.shared.domain.structures import Decimal, FilePath, Text
from animus.core.storage.domain.structures import File, UploadUrl
from animus.core.storage.interfaces import FileStorageProvider


class GcsFileStorageProvider(FileStorageProvider):
    _PDFS_DIR = Path(__file__).resolve().parents[6] / 'assets' / 'pdfs'
    client: Client

    def __init__(self) -> None:
        if Env.STORAGE_EMULATOR_HOST or Env.MODE == 'dev':
            self.client = Client.create_anonymous_client()
        else:
            self.client = Client()

    def generate_upload_url(self, file_path: FilePath) -> UploadUrl:
        msg = f'generate_upload_url is not implemented for file: {file_path.value}'
        raise NotImplementedError(msg)

    def get_file(self, file_path: FilePath) -> File:
        bucket = self.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
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
            key=Text.create(file_path.value),
            size_in_bytes=Decimal(value=size_in_bytes),
            mime_type=Text.create(mime_type),
        )

    def upload_files(self, file_paths: list[FilePath]) -> None:
        bucket = self.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
        if not bucket.exists():  # pyright: ignore[reportUnknownMemberType]
            self.client.create_bucket(bucket)  # pyright: ignore[reportUnknownMemberType]

        for file_path in file_paths:
            local_file_path = Path(file_path.value)
            if not local_file_path.exists():
                local_file_path = self._PDFS_DIR / Path(file_path.value).name
                if not local_file_path.exists():
                    msg = f'File not found: {file_path.value}'
                    raise FileNotFoundError(msg)

            blob = bucket.blob(file_path.value)  # pyright: ignore[reportUnknownMemberType]
            blob.upload_from_filename(str(local_file_path))  # pyright: ignore[reportUnknownMemberType]
