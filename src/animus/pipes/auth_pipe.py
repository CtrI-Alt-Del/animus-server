from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from animus.core.auth.interfaces import JwtProvider
from animus.core.shared.domain.errors import UnauthorizedError
from animus.core.shared.domain.structures import Id, Text
from animus.pipes.providers_pipe import ProvidersPipe

oauth2_scheme = HTTPBearer()


class AuthPipe:
    @staticmethod
    def get_current_account_id_from_token(
        token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
        jwt_provider: Annotated[JwtProvider, Depends(ProvidersPipe.get_jwt_provider)],
    ) -> Id:
        try:
            decoded_token = jwt_provider.decode(Text(token.credentials))
            sub = decoded_token.get('sub')
            
            if not sub:
                raise ValueError('Token subject nao encontrado')
                
            return Id(sub)
        except Exception as e:
            raise UnauthorizedError('Token invalido ou expirado') from e
