from abc import ABC
from typing import TYPE_CHECKING

from animus.core.shared.domain.decorators import entity

if TYPE_CHECKING:
    from animus.core.shared.domain.structures.id import Id


@entity
class Entity(ABC):
    id: 'Id'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id
