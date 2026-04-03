from typing import Annotated

from fastapi import Depends

from animus.core.shared.domain.structures import FilePath, Text
from animus.core.storage.interfaces import (
    DocxProvider,
    FileStorageProvider,
    PdfProvider,
)
from animus.core.storage.use_cases.get_document_content_use_case import (
    GetDocumentContentUseCase,
)
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.providers_pipe import ProvidersPipe


class StoragePipe:
    @staticmethod
    def get_document_content(
        file_path: Annotated[
            FilePath,
            Depends(IntakePipe.verify_petition_document_path_by_account),
        ],
        file_storage_provider: Annotated[
            FileStorageProvider,
            Depends(ProvidersPipe.get_file_storage_provider),
        ],
        pdf_provider: Annotated[PdfProvider, Depends(ProvidersPipe.get_pdf_provider)],
        docx_provider: Annotated[
            DocxProvider,
            Depends(ProvidersPipe.get_docx_provider),
        ],
    ) -> Text:
        use_case = GetDocumentContentUseCase(
            file_storage_provider=file_storage_provider,
            pdf_provider=pdf_provider,
            docx_provider=docx_provider,
        )
        return use_case.execute(file_path)
