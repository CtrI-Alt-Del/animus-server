import os
from pathlib import Path

from animus.constants import Env
from animus.core.shared.domain.structures import FilePath, Id
from animus.providers.storage.file_storage.gcs import GcsFileStorageProvider


class StorageSeeder:
    _PDFS_DIR = Path(__file__).resolve().parents[5] / 'assets' / 'pdfs'

    def __init__(self, storage_provider: GcsFileStorageProvider | None = None) -> None:
        storage_emulator_host = Env.STORAGE_EMULATOR_HOST
        if Env.MODE == 'dev' and not storage_emulator_host:
            storage_emulator_host = 'http://localhost:4443'

        if storage_emulator_host:
            os.environ['STORAGE_EMULATOR_HOST'] = storage_emulator_host

        self._storage_provider = storage_provider or GcsFileStorageProvider()

    def seed(self, analysis_id: Id) -> None:
        bucket = self._storage_provider.client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
        if bucket.exists():  # pyright: ignore[reportUnknownMemberType]
            bucket.delete(force=True)  # pyright: ignore[reportUnknownMemberType]

        self._storage_provider.client.create_bucket(bucket)  # pyright: ignore[reportUnknownMemberType]

        files_to_upload = [
            FilePath.create(
                f'intake/analises/{analysis_id.value}/petitions/{pdf_path.name}'
            )
            for pdf_path in sorted(self._PDFS_DIR.glob('*.pdf'))
        ]

        self._storage_provider.upload_files(file_paths=files_to_upload)
