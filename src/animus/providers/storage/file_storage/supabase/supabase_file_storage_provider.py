from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Mapping

from supabase import Client, create_client

from animus.constants import Env
from animus.core.shared.domain.errors.not_found_error import NotFoundError
from animus.core.shared.domain.structures import Decimal, FilePath, Text
from animus.core.storage.domain.structures import File, UploadUrl
from animus.core.storage.domain.structures.url import Url
from animus.core.storage.interfaces import FileStorageProvider


class SupabaseFileStorageProvider(FileStorageProvider):
    _PDFS_DIR = Path(__file__).resolve().parents[6] / "assets" / "pdfs"
    _supabase: Client

    def __init__(self) -> None:
        self._bucket = Env.SUPABASE_STORAGE_BUCKET
        self._supabase = create_client(
            Env.SUPABASE_URL,
            Env.SUPABASE_KEY,
        )

    def generate_upload_url(self, file_path: FilePath) -> UploadUrl:
        normalized_file_path = self._normalize_file_path(file_path.value)
        signed_upload_url = self._supabase.storage.from_(
            self._bucket
        ).create_signed_upload_url(
            path=normalized_file_path,
        )

        payload = cast("Mapping[str, object]", signed_upload_url)
        signed_url = str(
            payload.get("signed_url")
            or payload.get("signedUrl")
            or payload.get("signedURL")
            or ""
        )
        token = str(payload.get("token") or "")

        if not signed_url:
            msg = f"Failed to generate upload url for file path: {file_path.value}"
            raise ValueError(msg)

        return UploadUrl.create(
            url=Url.create(signed_url),
            token=Text.create(token),
            file_path=file_path,
        )

    def get_file(self, file_path: FilePath) -> File:
        normalized_file_path = self._normalize_file_path(file_path.value)
        try:
            file_content = self._supabase.storage.from_(self._bucket).download(
                path=normalized_file_path
            )
        except Exception as error:
            if self._is_not_found_error(error):
                raise NotFoundError(f"File not found: {file_path.value}") from error
            raise

        return File.create(
            value=file_content,
            key=Text.create(file_path.value),
            size_in_bytes=Decimal(value=float(len(file_content))),
            mime_type=Text.create("application/octet-stream"),
        )

    def upload_files(self, file_paths: list[FilePath]) -> None:
        for file_path in file_paths:
            local_file_path = Path(file_path.value)
            if not local_file_path.exists():
                local_file_path = self._PDFS_DIR / Path(file_path.value).name
                if not local_file_path.exists():
                    msg = f"File not found: {file_path.value}"
                    raise FileNotFoundError(msg)

            normalized_file_path = self._normalize_file_path(file_path.value)
            self._supabase.storage.from_(self._bucket).upload(
                path=normalized_file_path,
                file=local_file_path,
                file_options={"upsert": "true"},
            )

    def remove_files(self, file_paths: list[FilePath]) -> None:
        paths = [self._normalize_file_path(file_path.value) for file_path in file_paths]
        if not paths:
            return

        try:
            self._supabase.storage.from_(self._bucket).remove(paths)
        except Exception as error:
            if self._is_not_found_error(error):
                return
            raise

    @staticmethod
    def _is_not_found_error(error: Exception) -> bool:
        code = getattr(error, "code", None)
        if code == 404:
            return True

        status_code = getattr(error, "status_code", None)
        if status_code == 404:
            return True

        status_code = getattr(error, "statusCode", None)
        if status_code == "404" or status_code == 404:
            return True

        return error.__class__.__name__ == "NotFound"

    @staticmethod
    def _normalize_file_path(file_path: str) -> str:
        return file_path.lstrip("/")
