from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Integer, Text


@structure
class PdfOutlineItem(Structure):
    title: Text
    page_number: Integer

    @classmethod
    def create(cls, title: str, page_number: int) -> 'PdfOutlineItem':
        if page_number < 1:
            raise ValidationError(
                'Numero da pagina do outline deve ser maior ou igual a 1'
            )

        return cls(
            title=Text.create(title.strip()),
            page_number=Integer.create(page_number),
        )
