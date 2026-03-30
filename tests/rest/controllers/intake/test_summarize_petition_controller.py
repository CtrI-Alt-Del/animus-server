from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_analisyses_repository import (
    SqlalchemyAnalisysesRepository,
)
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_petitions_repository import (
    SqlalchemyPetitionsRepository,
)
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker
from animus.fakers.intake.entities.petitions_faker import PetitionsFaker
from animus.pipes.ai_pipe import AiPipe
from animus.pipes.providers_pipe import ProvidersPipe
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.gcs_fixtures import UploadGcsFileFixture


class FakePdfProvider:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls_count = 0

    def extract_content(self, pdf_file: object) -> Text:
        self.calls_count += 1
        return Text.create(self.content)


class FakeDocxProvider:
    def extract_content(self, docx_file: object) -> Text:
        raise AssertionError('DOCX provider should not be used in this scenario')


class FakeSummarizePetitionWorkflow:
    def __init__(self, response: PetitionSummaryDto) -> None:
        self.response = response
        self.received_petition_id: str | None = None
        self.received_document_content: Text | None = None

    def run(
        self,
        petition_id: str,
        petition_document_content: Text,
    ) -> PetitionSummaryDto:
        self.received_petition_id = petition_id
        self.received_document_content = petition_document_content
        return self.response


def _make_access_token(account_id: str) -> str:
    session = JoseJwtProvider().encode(Text.create(account_id))
    return session.access_token.value


def _create_analysis_and_petition(
    sqlalchemy_session_factory: sessionmaker[Session],
    account_id: str,
) -> tuple[str, str, str]:
    analysis = AnalysesFaker.fake(account_id=account_id)
    petition = PetitionsFaker.fake(
        analysis_id=analysis.id.value,
        document=PetitionDocumentDto(
            file_path='intake/analyses/01TEST/petitions/petition.pdf',
            name='petition.pdf',
        ),
    )
    session = sqlalchemy_session_factory()
    analyses_repository = SqlalchemyAnalisysesRepository(session)
    petitions_repository = SqlalchemyPetitionsRepository(session)

    analyses_repository.add(analysis)
    petitions_repository.add(petition)
    session.commit()
    session.close()

    return account_id, analysis.id.value, petition.id.value


class TestSummarizePetitionController:
    def test_should_return_201_and_petition_summary_when_petition_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        upload_gcs_file: UploadGcsFileFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        access_token = _make_access_token(account.id)
        _, _, petition_id = _create_analysis_and_petition(
            sqlalchemy_session_factory,
            account.id,
        )
        upload_gcs_file(
            'intake/analyses/01TEST/petitions/petition.pdf',
            b'%PDF-1.4 fake petition bytes',
            'application/pdf',
        )
        fake_pdf_provider = FakePdfProvider('Fatos e pedidos da peticao inicial')
        fake_workflow = FakeSummarizePetitionWorkflow(
            PetitionSummaryDto(
                case_summary='Resumo objetivo da peticao inicial',
                legal_issue='Controvérsia sobre inadimplemento contratual',
                central_question='Há inadimplemento apto a justificar condenação?',
                relevant_laws=['Código Civil, Art. 389', 'Código Civil, Art. 395'],
                key_facts=[
                    'Resumo dos fatos',
                    'Resumo dos fundamentos juridicos',
                ],
                search_terms=[
                    'inadimplemento contratual',
                    'obrigacao de pagar',
                    'responsabilidade contratual',
                ],
            )
        )
        app = client.app
        assert isinstance(app, FastAPI)
        app.dependency_overrides[ProvidersPipe.get_pdf_provider] = lambda: (
            fake_pdf_provider
        )
        app.dependency_overrides[ProvidersPipe.get_docx_provider] = lambda: (
            FakeDocxProvider()
        )
        app.dependency_overrides[AiPipe.get_summarize_petition_workflow] = lambda: (
            fake_workflow
        )

        response = client.post(
            f'/intake/petitions/{petition_id}/summary',
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 201
        assert response.json() == {
            'case_summary': 'Resumo objetivo da peticao inicial',
            'legal_issue': 'Controvérsia sobre inadimplemento contratual',
            'central_question': 'Há inadimplemento apto a justificar condenação?',
            'relevant_laws': [
                'Código Civil, Art. 389',
                'Código Civil, Art. 395',
            ],
            'key_facts': [
                'Resumo dos fatos',
                'Resumo dos fundamentos juridicos',
            ],
            'search_terms': [
                'inadimplemento contratual',
                'obrigacao de pagar',
                'responsabilidade contratual',
            ],
        }
        assert fake_pdf_provider.calls_count == 1
        assert fake_workflow.received_petition_id == petition_id
        assert fake_workflow.received_document_content == Text.create(
            'Fatos e pedidos da peticao inicial'
        )

    def test_should_return_404_when_petition_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        access_token = _make_access_token(account.id)

        response = client.post(
            '/intake/petitions/01ARZ3NDEKTSV4RRFFQ69G5FAV/summary',
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Peticao nao encontrada',
        }
