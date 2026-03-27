from pydantic import BaseModel


class PetitionSummaryOutput(BaseModel):
    content: str
    main_points: list[str]
