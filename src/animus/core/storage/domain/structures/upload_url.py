from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Text
from animus.core.storage.domain.structures.dtos import UploadUrlDto
from animus.core.storage.domain.structures.url import Url


@structure
class UploadUrl(Structure):
    url: Url
    token: Text
    file_path: Text

    @classmethod
    def create(cls, url: Url, token: Text, file_path: Text) -> 'UploadUrl':
        return cls(url=url, token=token, file_path=file_path)

    @property
    def dto(self) -> UploadUrlDto:
        return UploadUrlDto(
            url=self.url.value,
            token=self.token.value,
            file_path=self.file_path.value,
        )
