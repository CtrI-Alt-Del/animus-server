from fastapi import Request

from animus.core.shared.interfaces import Broker
from animus.pubsub.inngest.inngest_broker import InngestBroker


class PubSubPipe:
    @staticmethod
    def get_broker_from_request(request: Request) -> Broker:
        return InngestBroker(request.state.inngest_client)
