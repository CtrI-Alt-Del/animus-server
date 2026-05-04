import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

from google.api_core.exceptions import NotFound
from google.cloud.storage import Client

from animus.constants import Env
from animus.core.shared.domain.structures import Decimal, FilePath, Text
from animus.core.storage.domain.structures import File, UploadUrl
from animus.core.storage.domain.structures.url import Url
from animus.core.storage.interfaces import FileStorageProvider


class GcsFileStorageProvider(FileStorageProvider):
    _PDFS_DIR = Path(__file__).resolve().parents[6] / 'assets' / 'pdfs'
    client: Client

    def __init__(self) -> None:
        self._is_emulator = bool(Env.GCS_EMULATOR_HOST) or Env.MODE == 'dev'

        if self._is_emulator:
            os.environ['STORAGE_EMULATOR_HOST'] = self._normalize_emulator_base_url(
                Env.GCS_EMULATOR_HOST
            )
            self.client = Client.create_anonymous_client()
        else:
            os.environ.pop('STORAGE_EMULATOR_HOST', None)
            self.client = Client()

    def generate_upload_url(self, file_path: FilePath) -> UploadUrl:
        if self._is_emulator:
            upload_url_str = self._generate_emulator_upload_url(file_path)
        else:
            bucket_obj = self.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
            blob = bucket_obj.blob(file_path.value)  # pyright: ignore[reportUnknownMemberType]
            upload_url_str = blob.generate_signed_url(  # pyright: ignore[reportUnknownMemberType]
                method='PUT',
                version='v4',
                expiration=timedelta(minutes=15),
            )

        url_obj = Url.create(upload_url_str)
        token_obj = Text.create('')

        return UploadUrl.create(url=url_obj, token=token_obj, file_path=file_path)

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

    def remove_files(self, file_paths: list[FilePath]) -> None:
        bucket = self.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]

        for file_path in file_paths:
            blob = bucket.blob(file_path.value)  # pyright: ignore[reportUnknownMemberType]

            try:
                blob.delete()  # pyright: ignore[reportUnknownMemberType]
            except NotFound:
                continue

    def _generate_emulator_upload_url(self, file_path: FilePath) -> str:
        """
        Fake GCS local.

        O emulador testado não aceita:
            PUT /{bucket}/{object}

        Ele aceita upload pela JSON API:
            POST /upload/storage/v1/b/{bucket}/o?uploadType=media&name={object}

        Portanto, em dev/local, o cliente deve fazer POST com o arquivo no body.
        Em produção, o cliente continua fazendo PUT na signed URL real do GCS.
        """
        base_url = self._normalize_emulator_base_url(Env.GCS_EMULATOR_HOST)
        object_name = file_path.value.lstrip('/')

        query = urlencode(
            {
                'uploadType': 'media',
                'name': object_name,
            }
        )

        return f'{base_url}/upload/storage/v1/b/{Env.GCS_BUCKET_NAME}/o?{query}'

    @staticmethod
    def _normalize_emulator_base_url(host: str | None) -> str:
        if not host:
            return 'http://localhost:4443'

        normalized_host = host.strip().rstrip('/')

        if normalized_host.startswith('http://') or normalized_host.startswith(
            'https://'
        ):
            return normalized_host

        return f'http://{normalized_host}'
