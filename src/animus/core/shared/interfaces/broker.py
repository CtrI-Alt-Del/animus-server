from typing import Any, Protocol

from animus.core.shared.domain.abstracts import Event


class Broker(Protocol):
    def publish(self, event: Event[Any]) -> None: ...
