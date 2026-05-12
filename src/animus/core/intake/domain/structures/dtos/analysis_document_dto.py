from animus.core.shared.domain.decorators import dto


@dto
class AnalysisDocumentDto:
    analysis_id: str
    uploaded_at: str
    file_path: str
    name: str
