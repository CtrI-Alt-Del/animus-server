from typing import TypeVar

from animus.core.shared.domain.abstracts.entity import Entity
from animus.core.shared.domain.structures.logical import Logical
from animus.core.shared.domain.errors import AppError

EntityType = TypeVar('EntityType', bound=Entity)


class Aggregate[EntityType]:
    _entity: EntityType | None = None

    def __init__(self) -> None:
        pass

    @property
    def entity(self) -> EntityType:
        if self._entity is None:
            raise AppError('Aggregate Error', 'Entidade não encontrada')
        return self._entity

    @property
    def has_entity(self) -> Logical:
        return Logical.create(self._entity is not None)
