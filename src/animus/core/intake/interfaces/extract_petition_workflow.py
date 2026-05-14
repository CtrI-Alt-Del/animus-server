from typing import Protocol

from animus.core.intake.domain.structures.dtos.petition_extraction_dto import (
    PetitionExtractionDto,
)
from animus.core.storage.domain.structures import File


class ExtractPetitionWorkflow(Protocol):
    def run(self, pdf_file: File) -> PetitionExtractionDto: ...
