import os
from logging import getLogger
from typing import Any

from fastapi import FastAPI
from inngest import Inngest, fast_api

from animus.pubsub.inngest.jobs.auth import SendAccountVerificationEmailJob
from animus.pubsub.inngest.jobs.auth.send_password_reset_email_job import (
    SendPasswordResetEmailJob,
)
from animus.pubsub.inngest.jobs.intake import (
    GeneratePetitionDraftJob,
    GenerateSecondInstanceJudgmentDraftJob,
    RemovePetitionDocumentFileJob,
    SearchAnalysisPrecedentsJob,
    SeedAnalysesPrecedentsDatasetJob,
    SummarizeCaseAssessmentCaseJob,
    SummarizeFirstInstanceCaseJob,
    SummarizeSecondInstanceCaseJob,
    TriggerPetitionDraftGenerationJob,
    VectorizeAllPrecedentsJob,
    VectorizePrecedentsJob,
)
from animus.pubsub.inngest.jobs.notification import (
    SendCaseSummaryFinishedNotificationJob,
    SendPrecedentsSearchFinishedNotificationJob,
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
                *InngestPubSub.register_intake_jobs(inngest),
            ],
        )

        return inngest

    @staticmethod
    def register_notification_jobs(inngest: Inngest) -> list[Any]:
        return [
            SendAccountVerificationEmailJob.handle(inngest),
            SendPasswordResetEmailJob.handle(inngest),
            SendCaseSummaryFinishedNotificationJob.handle(inngest),
            SendPrecedentsSearchFinishedNotificationJob.handle(inngest),
        ]

    @staticmethod
    def register_intake_jobs(inngest: Inngest) -> list[Any]:
        return [
            SummarizeCaseAssessmentCaseJob.handle(inngest),
            SummarizeSecondInstanceCaseJob.handle(inngest),
            TriggerPetitionDraftGenerationJob.handle(inngest),
            GeneratePetitionDraftJob.handle(inngest),
            GenerateSecondInstanceJudgmentDraftJob.handle(inngest),
            RemovePetitionDocumentFileJob.handle(inngest),
            SearchAnalysisPrecedentsJob.handle(inngest),
            SeedAnalysesPrecedentsDatasetJob.handle(inngest),
            SummarizeFirstInstanceCaseJob.handle(inngest),
            VectorizeAllPrecedentsJob.handle(inngest),
            VectorizePrecedentsJob.handle(inngest),
        ]
