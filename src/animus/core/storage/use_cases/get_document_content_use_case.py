from animus.core.intake.domain.errors import (
    PetitionDocumentNotFoundError,
    UnreadablePetitionDocumentError,
    UnsupportedPetitionDocumentTypeError,
)
from animus.core.shared.domain.structures import FilePath, Text
from animus.core.storage.interfaces.docx_provider import DocxProvider
from animus.core.storage.interfaces.file_storage_provider import FileStorageProvider
from animus.core.storage.interfaces.pdf_provider import PdfProvider


class GetDocumentContentUseCase:
    def __init__(
        self,
        file_storage_provider: FileStorageProvider,
        pdf_provider: PdfProvider,
        docx_provider: DocxProvider,
    ) -> None:
        self._file_storage_provider = file_storage_provider
        self._pdf_provider = pdf_provider
        self._docx_provider = docx_provider

    @staticmethod
    def _is_not_found_error(error: Exception) -> bool:
        code = getattr(error, 'code', None)
        if code == 404:
            return True

        return error.__class__.__name__ == 'NotFound'

    def execute(self, file_path: FilePath) -> Text:
        file_extension = file_path.value.lower()
        if not file_extension.endswith(('.pdf', '.docx')):
            raise UnsupportedPetitionDocumentTypeError

        try:
            file = self._file_storage_provider.get_file(file_path)

            if file_extension.endswith('.pdf'):
                content = self._pdf_provider.extract_content(file)
            else:
                content = self._docx_provider.extract_content(file)
        except Exception as error:
            if self._is_not_found_error(error):
                raise PetitionDocumentNotFoundError from error

            raise UnreadablePetitionDocumentError from error

        if not content.value.strip():
            raise UnreadablePetitionDocumentError

        return content
