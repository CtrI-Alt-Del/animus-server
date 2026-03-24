from typing import Protocol

from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.structures.text import Text


class OAuthProvider(Protocol):
    def get_user_info(self,token_id:Text) -> tuple[Text,Email]:...
