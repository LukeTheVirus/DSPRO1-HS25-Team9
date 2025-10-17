from .document_data import DocumentData


class DocumentResult:
    document_data: DocumentData
    score: float

    def __init__(self, document_data: DocumentData, score: float):
        self.document_data = document_data
        self.score = score
