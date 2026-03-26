from faker import Faker

from animus.core.shared.domain.structures import Id

ULID_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'


class IdFaker:
    _faker = Faker()

    @staticmethod
    def fake(id_value: str | None = None) -> Id:
        value = id_value or IdFaker._faker.pystr(
            min_chars=26,
            max_chars=26,
            allowed_chars=ULID_ALPHABET,
        )
        return Id.create(value)
