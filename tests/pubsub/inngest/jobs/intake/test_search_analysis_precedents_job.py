import time
from typing import cast
from datetime import UTC, datetime
from typing import Any

import pytest
from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.ai.agno.workflows.intake import AgnoSynthesizeAnalysisPrecedentsWorkflow
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.intake.use_cases import SearchAnalysisPrecedentsUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel
from animus.database.sqlalchemy.models.intake.analysis_precedent_model import (
    AnalysisPrecedentModel,
)
from animus.database.sqlalchemy.models.intake.petition_model import PetitionModel
from animus.database.sqlalchemy.models.intake.petition_summary_model import (
    PetitionSummaryModel,
)
from animus.database.sqlalchemy.models.intake.precedent_model import PrecedentModel
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pubsub.inngest.jobs.intake.search_analysis_precedents_job import (
    SearchAnalysisPrecedentsJob,
)


def _seed_analysis_with_petition_summary(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> dict[str, str]:
    analysis_id = Id.create().value
    petition_id = Id.create().value
    precedent_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise de teste',
            account_id=Id.create().value,
            folder_id=None,
            status=AnalysisStatusValue.WAITING_PETITION.value,
            is_archived=False,
        )
    )
    session.add(
        PetitionModel(
            id=petition_id,
            analysis_id=analysis_id,
            uploaded_at=datetime.now(UTC),
            document_file_path='petitions/test.pdf',
            document_name='test.pdf',
        )
    )
    session.add(
        PetitionSummaryModel(
            petition_id=petition_id,
            case_summary='Resumo do caso',
            legal_issue='Questao juridica',
            central_question='Pergunta central',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['termo 1'],
        )
    )
    session.add(
        PrecedentModel(
            id=precedent_id,
            court='STF',
            kind='RG',
            number=101,
            status='vigente',
            enunciation='Enunciado do precedente',
            thesis='Tese do precedente',
            last_updated_in_pangea_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
        'precedent_id': precedent_id,
    }


def _get_analysis_status(
    sqlalchemy_session_factory: sessionmaker[Session],
    analysis_id: str,
) -> str:
    session = sqlalchemy_session_factory()
    try:
        model = session.get(AnalysisModel, analysis_id)
        assert model is not None
        return model.status
    finally:
        session.close()


def _get_analysis_precedents(
    sqlalchemy_session_factory: sessionmaker[Session],
    analysis_id: str,
) -> list[AnalysisPrecedentModel]:
    session = sqlalchemy_session_factory()
    try:
        return list(
            session.scalars(
                select(AnalysisPrecedentModel).where(
                    AnalysisPrecedentModel.analysis_id == analysis_id
                )
            ).all()
        )
    finally:
        session.close()


def _wait_until(predicate: Any, *, timeout_seconds: float = 60) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)

    msg = 'condition not satisfied before timeout'
    raise AssertionError(msg)


class TestSearchAnalysisPrecedentsJob:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_event_with_real_inngest_dev_server(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_analysis_with_petition_summary(sqlalchemy_session_factory)
        captured_steps: list[dict[str, Any]] = []

        async def _search_precedents(payload: Any) -> list[dict[str, Any]]:
            captured_steps.append(
                {
                    'step': 'search_precedents',
                    'analysis_id': payload.analysis_id,
                    'courts': payload.courts,
                    'precedent_kinds': payload.precedent_kinds,
                    'limit': payload.limit,
                }
            )
            return [
                {
                    'analysis_id': payload.analysis_id,
                    'precedent': {
                        'id': seeded_data['precedent_id'],
                        'identifier': {
                            'court': 'STF',
                            'kind': 'RG',
                            'number': 101,
                        },
                        'status': 'vigente',
                        'enunciation': 'Enunciado do precedente',
                        'thesis': 'Tese do precedente',
                        'last_updated_in_pangea_at': datetime.now(UTC).isoformat(),
                    },
                    'applicability_percentage': 84.5,
                    'synthesis': None,
                    'is_chosen': False,
                }
            ]

        async def _generate_syntheses_and_persist(
            payload: Any,
            analysis_precedents_data: list[dict[str, Any]],
        ) -> None:
            captured_steps.append(
                {
                    'step': 'generate_syntheses_and_persist',
                    'analysis_id': payload.analysis_id,
                    'analysis_precedents_data': analysis_precedents_data,
                }
            )

        monkeypatch.setattr(
            SearchAnalysisPrecedentsJob,
            '_search_precedents',
            _search_precedents,
        )
        monkeypatch.setattr(
            SearchAnalysisPrecedentsJob,
            '_generate_syntheses_and_persist',
            _generate_syntheses_and_persist,
        )

        response = inngest_runtime.post_event(
            name='intake/analysis.precedents.search.requested',
            data={
                'analysis_id': seeded_data['analysis_id'],
                'courts': ['STF'],
                'precedent_kinds': ['RG'],
                'limit': 5,
            },
        )

        assert response.status == 200

        _wait_until(lambda: len(captured_steps) == 2)

        assert captured_steps == [
            {
                'step': 'search_precedents',
                'analysis_id': seeded_data['analysis_id'],
                'courts': ['STF'],
                'precedent_kinds': ['RG'],
                'limit': 5,
            },
            {
                'step': 'generate_syntheses_and_persist',
                'analysis_id': seeded_data['analysis_id'],
                'analysis_precedents_data': [
                    {
                        'analysis_id': seeded_data['analysis_id'],
                        'precedent': {
                            'id': seeded_data['precedent_id'],
                            'identifier': {
                                'court': 'STF',
                                'kind': 'RG',
                                'number': 101,
                            },
                            'status': 'vigente',
                            'enunciation': 'Enunciado do precedente',
                            'thesis': 'Tese do precedente',
                            'last_updated_in_pangea_at': captured_steps[1][
                                'analysis_precedents_data'
                            ][0]['precedent']['last_updated_in_pangea_at'],
                        },
                        'applicability_percentage': 84.5,
                        'synthesis': None,
                        'is_chosen': False,
                    }
                ],
            },
        ]

    def test_should_persist_waiting_precedent_choise_status_when_sync_steps_succeed(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.search_analysis_precedents_job',
            fromlist=['_Payload'],
        )
        job_class = cast('Any', SearchAnalysisPrecedentsJob)
        payload_factory = job_module._Payload  # noqa: SLF001
        search_precedents_sync = job_class._search_precedents_sync  # noqa: SLF001
        generate_syntheses_and_persist_sync_name = (
            '_generate_syntheses_and_persist_sync'
        )
        generate_syntheses_and_persist_sync = getattr(
            job_class,
            generate_syntheses_and_persist_sync_name,
        )
        seeded_data = _seed_analysis_with_petition_summary(sqlalchemy_session_factory)
        payload = payload_factory(
            analysis_id=seeded_data['analysis_id'],
            courts=['STF'],
            precedent_kinds=['RG'],
            limit=5,
        )

        def _execute(
            _self: SearchAnalysisPrecedentsUseCase,
            *,
            analysis_id: str,
            dto: Any,
        ) -> list[AnalysisPrecedentDto]:
            return [
                AnalysisPrecedentDto(
                    analysis_id=analysis_id,
                    precedent=PrecedentDto(
                        id=seeded_data['precedent_id'],
                        identifier=PrecedentIdentifierDto(
                            court='STF',
                            kind='RG',
                            number=101,
                        ),
                        status='vigente',
                        enunciation='Enunciado do precedente',
                        thesis='Tese do precedente',
                        last_updated_in_pangea_at=datetime.now(UTC).isoformat(),
                    ),
                    applicability_percentage=84.5,
                    synthesis=None,
                    is_chosen=False,
                )
            ]

        def _run(
            _self: AgnoSynthesizeAnalysisPrecedentsWorkflow,
            *,
            petition_summary: Any,
            analysis_precedents: list[AnalysisPrecedentDto],
        ) -> ListResponse[AnalysisPrecedent]:
            return ListResponse(
                items=[
                    AnalysisPrecedent.create(
                        AnalysisPrecedentDto(
                            analysis_id=analysis_precedent.analysis_id,
                            precedent=analysis_precedent.precedent,
                            applicability_percentage=(
                                analysis_precedent.applicability_percentage
                            ),
                            synthesis='Sintese final do precedente',
                            is_chosen=analysis_precedent.is_chosen,
                        )
                    )
                    for analysis_precedent in analysis_precedents
                ]
            )

        monkeypatch.setattr(SearchAnalysisPrecedentsUseCase, 'execute', _execute)
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )
        monkeypatch.setattr(
            AgnoSynthesizeAnalysisPrecedentsWorkflow,
            '__init__',
            lambda *args, **kwargs: None,  # type: ignore
        )
        monkeypatch.setattr(AgnoSynthesizeAnalysisPrecedentsWorkflow, 'run', _run)

        analysis_precedents_data = search_precedents_sync(payload)

        assert (
            _get_analysis_status(
                sqlalchemy_session_factory,
                seeded_data['analysis_id'],
            )
            == AnalysisStatusValue.SEARCHING_PRECEDENTS.value
        )

        generate_syntheses_and_persist_sync(payload, analysis_precedents_data)

        analysis_precedents = _get_analysis_precedents(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert (
            _get_analysis_status(
                sqlalchemy_session_factory,
                seeded_data['analysis_id'],
            )
            == AnalysisStatusValue.WAITING_PRECEDENT_CHOISE.value
        )
        assert len(analysis_precedents) == 1
        assert analysis_precedents[0].precedent_id == seeded_data['precedent_id']
        assert analysis_precedents[0].synthesis == 'Sintese final do precedente'
        assert analysis_precedents[0].is_chosen is False

    def test_should_persist_failed_status_when_sync_failure_handler_runs(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.search_analysis_precedents_job',
            fromlist=['_Payload'],
        )
        job_class = cast('Any', SearchAnalysisPrecedentsJob)
        payload_factory = job_module._Payload  # noqa: SLF001
        mark_analysis_as_failed_sync = job_class._mark_analysis_as_failed_sync  # noqa: SLF001
        seeded_data = _seed_analysis_with_petition_summary(sqlalchemy_session_factory)
        payload = payload_factory(
            analysis_id=seeded_data['analysis_id'],
            courts=['STF'],
            precedent_kinds=['RG'],
            limit=5,
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        mark_analysis_as_failed_sync(payload)

        assert (
            _get_analysis_status(
                sqlalchemy_session_factory,
                seeded_data['analysis_id'],
            )
            == AnalysisStatusValue.FAILED.value
        )
        assert (
            _get_analysis_precedents(
                sqlalchemy_session_factory,
                seeded_data['analysis_id'],
            )
            == []
        )
