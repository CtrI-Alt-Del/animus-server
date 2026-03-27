from dataclasses import fields, is_dataclass
from pydantic.dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Structure:
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        if not is_dataclass(self) or not is_dataclass(other):
            return NotImplemented

        return all(
            getattr(self, f.name) == getattr(other, f.name) for f in fields(self)
        )
