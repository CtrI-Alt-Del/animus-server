import re

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Password(Structure):
    value: str

    @staticmethod
    def create(value: str) -> 'Password':
        if len(value) < 8:
            raise ValidationError('Senha deve ter pelo menos 8 caracteres')

        if not re.search(r'[A-Z]', value):
            raise ValidationError('Senha deve ter pelo menos uma letra maiuscula')

        if not re.search(r'\d', value):
            raise ValidationError('Senha deve ter pelo menos um numero')

        return Password(value=value)
