from typing import Annotated
from pydantic import Field

from animus.core.shared.domain.structures.id import ULID_REGEX


IdSchema = Annotated[str, Field(pattern=ULID_REGEX)]
