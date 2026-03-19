from typing import Protocol

from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.shared.domain.structures import Text


class JwtProvider(Protocol):
    def encode(self, subject: Text) -> SessionDto: ...

    def decode(self, token: Text) -> dict[str, str]: ...
