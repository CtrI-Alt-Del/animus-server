from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Text


@structure
class ExtractedCourtDocumentPieces(Structure):
    sentenca: Text
    apelacao: Text
    contrarrazoes: Text | None

    @classmethod
    def create(
        cls,
        sentenca: str,
        apelacao: str,
        contrarrazoes: str | None = None,
    ) -> 'ExtractedCourtDocumentPieces':
        return cls(
            sentenca=Text.create(sentenca),
            apelacao=Text.create(apelacao),
            contrarrazoes=(
                Text.create(contrarrazoes) if contrarrazoes is not None else None
            ),
        )
