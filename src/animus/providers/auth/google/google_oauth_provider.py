from google.auth.transport import requests
from google.oauth2 import id_token

from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces.oauth_provider import OAuthProvider
from animus.core.shared.domain.structures.text import Text


class GoogleOAuthProvider(OAuthProvider):
    def __init__(self, client_id: str) -> None:
        self._client_id = client_id

    def get_user_info(self, token_id: Text) -> tuple[Text, Email]:
        request = requests.Request()
        id_info = id_token.verify_oauth2_token(  # type: ignore[attr-defined]
            token_id.value,
            request,
            self._client_id,
        )
        name: str | None = id_info.get('name')
        email: str | None = id_info.get('email')

        if not name or not email:
            msg = 'Invalid token: missing name or email'
            raise ValueError(msg)

        return Text.create(name), Email.create(email)
