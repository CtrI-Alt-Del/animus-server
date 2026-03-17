from pydantic.dataclasses import dataclass
from typing import dataclass_transform


@dataclass_transform(frozen_default=False, kw_only_default=True)
def entity[T](cls: type[T]) -> type[T]:
    return dataclass(frozen=False, kw_only=True, eq=False)(cls)  # type: ignore
