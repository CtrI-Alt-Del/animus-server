from typing import Protocol

from animus.core.auth.domain.structures import Session
from animus.core.shared.domain.structures import Text


class JwtProvider(Protocol):
    def encode(self, subject: Text) -> Session: ...

    def decode(self, token: Text) -> dict[str, str]: ...
