from pydantic.dataclasses import dataclass
from typing import dataclass_transform


@dataclass_transform(frozen_default=True, kw_only_default=True)
def response[T](cls: type[T]) -> type[T]:
    return dataclass(frozen=True, kw_only=True)(cls)  # type: ignore
