from animus.core.shared.domain.abstracts.structure import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures.dtos.image_dto import ImageDto
from animus.core.shared.domain.structures.text import Text


@structure
class Image(Structure):
    key: Text
    name: Text

    @classmethod
    def create(cls, dto: ImageDto) -> 'Image':
        return cls(key=Text.create(dto.key), name=Text.create(dto.name))

    @property
    def dto(self) -> ImageDto:
        return ImageDto(key=self.key.value, name=self.name.value)
