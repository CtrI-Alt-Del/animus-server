from abc import ABC
from dataclasses import asdict, dataclass
from typing import Any, cast


@dataclass(frozen=True)
class Event[Payload](ABC):
    name: str
    payload: Payload

    @property
    def payload_data(self) -> dict[str, Any]:
        if self.payload is None:
            return {}
        return asdict(cast('Any', self.payload))
