import httpx

from animus.constants import Env
from animus.core.notification.interfaces import PushNotificationProvider
from animus.core.shared.domain.structures import Id


class OneSignalPushNotificationProvider(PushNotificationProvider):
    def send_petition_summary_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
    ) -> None:
        title = 'Analise de peticao concluida'
        body = 'O resumo da sua peticao ja esta disponivel.'
        data = {
            'type': 'petition_summary_finished',
            'analysis_id': analysis_id.value,
        }
        self._send_push(recipient_id, title, body, data)

    def send_precedents_search_finished_message(
        self,
        recipient_id: Id,
        analysis_id: Id,
    ) -> None:
        title = 'Busca de precedentes finalizada'
        body = 'A busca e sintese de precedentes para sua analise foi concluida.'
        data = {
            'type': 'precedents_search_finished',
            'analysis_id': analysis_id.value,
        }
        self._send_push(recipient_id, title, body, data)

    def _send_push(
        self,
        recipient_id: Id,
        title: str,
        body: str,
        data: dict[str, str],
    ) -> None:
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Basic {Env.ONESIGNAL_REST_API_KEY}',
        }
        payload = {
            'app_id': Env.ONESIGNAL_APP_ID,
            'include_external_user_ids': [recipient_id.value],
            'headings': {'en': title, 'pt': title},
            'contents': {'en': body, 'pt': body},
            'data': data,
        }
        url = 'https://onesignal.com/api/v1/notifications'

        with httpx.Client() as client:
            client.post(url, json=payload, headers=headers)
