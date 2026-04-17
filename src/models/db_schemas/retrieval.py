from pydantic import BaseModel

class RetrievedDocument(BaseModel):
    """
    Schema for RAG retrieval results.
    Standardizes the format of snippets sent to the LLM.
    """
    text: str
    score: float
    metadata: dict = {}
