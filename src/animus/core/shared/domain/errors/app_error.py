class AppError(Exception):
    def __init__(self, title: str, message: str) -> None:
        super().__init__(message)
        self.title = title
        self.message = message

    def __str__(self) -> str:
        return f'{self.title}: {self.message}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}: {self.title}: {self.message}'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AppError):
            return NotImplemented
        return self.title == other.title and self.message == other.message
