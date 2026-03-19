from typing import Protocol

from animus.core.shared.domain.structures import Logical, Text


class HashProvider(Protocol):
    def generate(self, password: Text) -> Text: ...

    def verify(self, password: Text, hashed_password: Text) -> Logical: ...
