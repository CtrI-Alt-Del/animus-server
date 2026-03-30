import re

from animus.core.shared.domain.abstracts.structure import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures.logical import Logical

_VALID_FILE_PATH_RE = re.compile(
    r'^(?!\s)(?!.*\s$)(?!/)(?!.*//)(?!.*(?:^|/)\.\.(?:/|$))(?:[^/\x00]+/)*[^/\x00]+\.[^/\x00.]+$'
)


@structure
class FilePath(Structure):
    value: str

    @classmethod
    def create(cls, value: str) -> "FilePath":
        if _VALID_FILE_PATH_RE.fullmatch(value) is None:
            raise ValidationError(f'Caminho de arquivo invalido: {value}')

        return cls(value=value)

    def is_pdf_file(self) -> Logical:
        return Logical.create(self.value.lower().endswith(".pdf"))

    def is_docx_file(self) -> Logical:
        return Logical.create(self.value.lower().endswith(".docx"))
