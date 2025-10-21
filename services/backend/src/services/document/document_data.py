class DocumentData:
    identifier: str
    hash: str
    text_content: str

    def __init__(self, identifier: str, hash: str, text_content: str):
        self.identifier = identifier
        self.hash = hash
        self.text_content = text_content
