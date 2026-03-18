from pydantic.dataclasses import dataclass
from typing import dataclass_transform


@dataclass_transform(frozen_default=False, kw_only_default=True)
def dto[T](cls: type[T]) -> type[T]:
    return dataclass(kw_only=True)(cls)  # type: ignore[reportReturnType]
