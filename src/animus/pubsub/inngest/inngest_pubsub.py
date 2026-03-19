import os
from logging import getLogger
from typing import Any

from fastapi import FastAPI
from inngest import Inngest, fast_api

from animus.pubsub.inngest.jobs.auth import SendAccountVerificationEmailJob


class InngestPubSub:
    @staticmethod
    def register(app: FastAPI) -> Inngest:
        inngest = Inngest(
            app_id='animus-server',
            is_production=(
                os.getenv('INNGEST_DEV') is None
                and bool(os.getenv('INNGEST_SIGNING_KEY'))
            ),
            logger=getLogger(name='uvicorn'),
        )

        fast_api.serve(
            app,
            client=inngest,
            functions=[
                *InngestPubSub.register_notification_jobs(inngest),
            ],
        )

        return inngest

    @staticmethod
    def register_notification_jobs(inngest: Inngest) -> list[Any]:
        return [
            SendAccountVerificationEmailJob.handle(inngest),
        ]
