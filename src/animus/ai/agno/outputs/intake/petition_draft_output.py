from pydantic import BaseModel


class PetitionDraftOutput(BaseModel):
    structured_facts: str
    legal_grounds: str
    central_thesis: str
    requests: list[str]
    precedent_citations: list[str]
