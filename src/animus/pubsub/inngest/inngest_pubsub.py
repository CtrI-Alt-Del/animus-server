import os
from logging import getLogger
from typing import Any

from fastapi import FastAPI
from inngest import Inngest, fast_api

from animus.pubsub.inngest.jobs.auth import SendAccountVerificationEmailJob
from animus.pubsub.inngest.jobs.intake.vectorize_precedents_job import (
    VectorizePrecedentsJob,
)


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
                *InngestPubSub.register_vectorize_precedents_job(inngest),
            ],
        )

        return inngest

    @staticmethod
    def register_notification_jobs(inngest: Inngest) -> list[Any]:
        return [
            SendAccountVerificationEmailJob.handle(inngest),
        ]

    @staticmethod
    def register_vectorize_precedents_job(inngest: Inngest) -> list[Any]:
        return [VectorizePrecedentsJob.handle(inngest)]
