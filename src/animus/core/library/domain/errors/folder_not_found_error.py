from animus.core.shared.domain.errors import NotFoundError


class FolderNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Pasta nao encontrada')
