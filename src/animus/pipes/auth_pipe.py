from typing import Annotated

from fastapi import Depends, Header

from animus.core.auth.interfaces import AccountsRepository, JwtProvider
from animus.core.shared.domain.errors import AuthError
from animus.core.shared.domain.structures import Id, Text
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.providers_pipe import ProvidersPipe


class AuthPipe:
    @staticmethod
    def get_account_id_from_request(
        authorization: Annotated[str, Header(alias='Authorization')],
        jwt_provider: Annotated[JwtProvider, Depends(ProvidersPipe.get_jwt_provider)],
        accounts_repository: Annotated[
            AccountsRepository,
            Depends(DatabasePipe.get_accounts_repository_from_request),
        ],
    ) -> Id:
        if not authorization.startswith('Bearer '):
            raise AuthError('Header Authorization invalido')

        token = authorization.removeprefix('Bearer ').strip()
        if not token:
            raise AuthError('Token de acesso ausente')

        try:
            payload = jwt_provider.decode(Text.create(token))
        except Exception as error:
            raise AuthError('Token de acesso invalido') from error

        if payload.get('type') != 'access':
            raise AuthError('Tipo de token invalido')

        subject = payload.get('sub')
        if not subject:
            raise AuthError('Token sem subject')

        account_id = Id.create(subject)
        account = accounts_repository.find_by_id(account_id)
        if account is None:
            raise AuthError('Conta autenticada nao encontrada')

        return account_id
