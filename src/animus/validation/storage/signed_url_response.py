from pydantic import BaseModel


class SignedUrlResponse(BaseModel):
    url: str
    headers: dict[str, str]
