from pydantic import BaseModel


class PetitionExtractionOutput(BaseModel):
    first_page: int | None = None
    last_page: int | None = None
