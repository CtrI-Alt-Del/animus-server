from pwdlib import PasswordHash

from animus.core.auth.interfaces import HashProvider
from animus.core.shared.domain.structures import Logical, Text


class Argon2idHashProvider(HashProvider):
    _password_hash = PasswordHash.recommended()

    def generate(self, password: Text) -> Text:
        hashed_password = self._password_hash.hash(password.value)
        return Text.create(hashed_password)

    def verify(self, password: Text, hashed_password: Text) -> Logical:
        is_valid = self._password_hash.verify(password.value, hashed_password.value)
        return Logical.create(is_valid)
