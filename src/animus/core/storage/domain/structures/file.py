from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Decimal, Text
from animus.core.storage.domain.structures.dtos import FileDto


@structure
class File(Structure):
    value: bytes
    key: Text
    size_in_bytes: Decimal
    mime_type: Text

    @classmethod
    def create(
        cls,
        value: bytes,
        key: Text,
        size_in_bytes: Decimal,
        mime_type: Text,
    ) -> 'File':
        return cls(
            value=value,
            key=key,
            size_in_bytes=size_in_bytes,
            mime_type=mime_type,
        )

    @property
    def dto(self) -> FileDto:
        return FileDto(
            value=self.value,
            key=self.key.value,
            size_in_bytes=self.size_in_bytes.value,
            mime_type=self.mime_type.value,
        )
